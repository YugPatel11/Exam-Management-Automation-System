"""
Views for Academic Year Management.

Provides:
- AcademicYear CRUD (list, create, detail dashboard, update, delete)
- Import Wizard (upload → preview → confirm)
- Semester Detail
- API endpoints for cascading dropdowns
"""
import os
import uuid
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, View
from django.db.models import Q, Count, Sum
from django.db.models.deletion import ProtectedError

from apps.core.mixins import ExamCoordinatorRequiredMixin
from apps.academic.models import (
    AcademicYear, Semester, SemesterSubject,
    MarksComponent, AcademicStructureImport,
)
from apps.academic.forms import AcademicYearForm, AcademicStructureUploadForm
from apps.academic.services import AcademicStructureImportService


# ═══════════════════════════════════════════════
# ACADEMIC YEAR CRUD
# ═══════════════════════════════════════════════

class AcademicYearListView(ExamCoordinatorRequiredMixin, ListView):
    """List all Academic Years with stats cards."""
    model = AcademicYear
    template_name = 'academic/year_list.html'
    context_object_name = 'academic_years'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().annotate(
            semester_count=Count('semesters', distinct=True),
            subject_count=Count('semesters__semester_subjects', distinct=True),
        )

        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(description__icontains=query))

        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        return qs


class AcademicYearCreateView(ExamCoordinatorRequiredMixin, CreateView):
    """Create a new Academic Year."""
    model = AcademicYear
    form_class = AcademicYearForm
    template_name = 'academic/year_form.html'

    def get_success_url(self):
        return reverse_lazy('academic:year_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Create Academic Year'
        ctx['cancel_url'] = reverse_lazy('academic:year_list')
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Academic Year created successfully.")
        return super().form_valid(form)


class AcademicYearDetailView(ExamCoordinatorRequiredMixin, DetailView):
    """
    Dashboard view for a single Academic Year.
    Shows stats, semester breakdown, import history.
    """
    model = AcademicYear
    template_name = 'academic/year_detail.html'
    context_object_name = 'academic_year'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ay = self.object

        # Semesters with subject counts
        semesters = Semester.objects.filter(academic_year=ay).annotate(
            subject_count=Count('semester_subjects'),
            total_marks=Sum('semester_subjects__marks_components__max_marks'),
        ).order_by('number')

        # Import history
        imports = AcademicStructureImport.objects.filter(academic_year=ay).order_by('-created_at')[:10]

        # Exam count for this AY
        from apps.exams.models import Exam
        exam_count = Exam.objects.filter(academic_year=ay.name).count()
        # Also count exams linked via FK
        exam_count += Exam.objects.filter(academic_year_ref=ay).exclude(academic_year=ay.name).count()

        ctx.update({
            'semesters': semesters,
            'imports': imports,
            'total_semesters': semesters.count(),
            'total_subjects': ay.total_subjects,
            'total_components': ay.total_components,
            'total_exams': exam_count,
            'breadcrumbs': [
                {'label': 'Academic Years', 'url': reverse('academic:year_list')},
                {'label': ay.name, 'url': None},
            ],
        })
        return ctx


class AcademicYearUpdateView(ExamCoordinatorRequiredMixin, UpdateView):
    """Edit an Academic Year."""
    model = AcademicYear
    form_class = AcademicYearForm
    template_name = 'academic/year_form.html'

    def get_success_url(self):
        return reverse_lazy('academic:year_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Edit Academic Year: {self.object.name}'
        ctx['cancel_url'] = reverse_lazy('academic:year_detail', kwargs={'pk': self.object.pk})
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Academic Year updated successfully.")
        return super().form_valid(form)


class AcademicYearDeleteView(ExamCoordinatorRequiredMixin, DeleteView):
    """Delete an Academic Year."""
    model = AcademicYear
    template_name = 'master_data/confirm_delete.html'
    success_url = reverse_lazy('academic:year_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Delete Academic Year'
        ctx['cancel_url'] = reverse_lazy('academic:year_detail', kwargs={'pk': self.object.pk})
        ctx['item_name'] = f"Academic Year {self.object.name}"
        ctx['warning'] = (
            "This will permanently delete all semesters, subjects, marks components, "
            "and import history associated with this academic year."
        )
        return ctx

    def form_valid(self, form):
        try:
            name = self.object.name
            response = super().form_valid(form)
            messages.success(self.request, f"Academic Year {name} deleted.")
            return response
        except ProtectedError:
            messages.error(
                self.request,
                "Cannot delete this Academic Year because it has linked exams or marks data. "
                "Archive it instead."
            )
            return redirect('academic:year_detail', pk=self.object.pk)


# ═══════════════════════════════════════════════
# IMPORT WIZARD
# ═══════════════════════════════════════════════

class ImportWizardUploadView(ExamCoordinatorRequiredMixin, View):
    """Step 1: Upload the CSV/Excel file."""

    def get(self, request, pk):
        academic_year = get_object_or_404(AcademicYear, pk=pk)
        form = AcademicStructureUploadForm()

        # Check if AY already has data
        has_existing = Semester.objects.filter(academic_year=academic_year).exists()

        context = {
            'step': 1,
            'academic_year': academic_year,
            'form': form,
            'has_existing_data': has_existing,
            'breadcrumbs': [
                {'label': 'Academic Years', 'url': reverse('academic:year_list')},
                {'label': academic_year.name, 'url': reverse('academic:year_detail', kwargs={'pk': pk})},
                {'label': 'Import Structure', 'url': None},
            ],
        }
        return render(request, 'academic/import_wizard.html', context)

    def post(self, request, pk):
        academic_year = get_object_or_404(AcademicYear, pk=pk)
        form = AcademicStructureUploadForm(request.POST, request.FILES)

        if form.is_valid():
            uploaded_file = form.cleaned_data['structure_file']

            # Save file temporarily
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_imports'))
            ext = os.path.splitext(uploaded_file.name)[1]
            temp_name = fs.save(f"academic_import_{uuid.uuid4().hex}{ext}", uploaded_file)

            # Store in session
            request.session['academic_import_file'] = temp_name
            request.session['academic_import_original_name'] = uploaded_file.name
            request.session['academic_import_ay_id'] = str(pk)

            return redirect('academic:import_preview', pk=pk)

        context = {
            'step': 1,
            'academic_year': academic_year,
            'form': form,
            'breadcrumbs': [
                {'label': 'Academic Years', 'url': reverse('academic:year_list')},
                {'label': academic_year.name, 'url': reverse('academic:year_detail', kwargs={'pk': pk})},
                {'label': 'Import Structure', 'url': None},
            ],
        }
        return render(request, 'academic/import_wizard.html', context)


class ImportWizardPreviewView(ExamCoordinatorRequiredMixin, View):
    """Step 2: Preview validation results."""

    def get(self, request, pk):
        academic_year = get_object_or_404(AcademicYear, pk=pk)

        filename = request.session.get('academic_import_file')
        original_name = request.session.get('academic_import_original_name', 'unknown')

        if not filename:
            messages.error(request, "No import file found. Please start over.")
            return redirect('academic:import_upload', pk=pk)

        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_imports'))
        if not fs.exists(filename):
            messages.error(request, "Import file expired or missing. Please start over.")
            return redirect('academic:import_upload', pk=pk)

        # Run validation
        with fs.open(filename, 'rb') as f:
            service = AcademicStructureImportService(f, original_name, academic_year)
            summary = service.validate()

        context = {
            'step': 2,
            'academic_year': academic_year,
            'summary': summary,
            'filename': filename,
            'original_name': original_name,
            'breadcrumbs': [
                {'label': 'Academic Years', 'url': reverse('academic:year_list')},
                {'label': academic_year.name, 'url': reverse('academic:year_detail', kwargs={'pk': pk})},
                {'label': 'Import Preview', 'url': None},
            ],
        }
        return render(request, 'academic/import_wizard.html', context)


class ImportWizardProcessView(ExamCoordinatorRequiredMixin, View):
    """Step 3: Confirm and commit the import."""

    def post(self, request, pk):
        academic_year = get_object_or_404(AcademicYear, pk=pk)

        filename = request.session.get('academic_import_file')
        original_name = request.session.get('academic_import_original_name', 'unknown')

        if not filename:
            messages.error(request, "No import session found.")
            return redirect('academic:import_upload', pk=pk)

        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_imports'))
        if not fs.exists(filename):
            messages.error(request, "Import file missing. Please start over.")
            return redirect('academic:import_upload', pk=pk)

        try:
            with fs.open(filename, 'rb') as f:
                service = AcademicStructureImportService(f, original_name, academic_year)
                service.validate()
                import_record = service.process_import(imported_by=request.user)

            if import_record.status == AcademicStructureImport.ImportStatus.SUCCESS:
                summary = import_record.summary
                messages.success(
                    request,
                    f"Import successful! Created {summary.get('semesters_created', 0)} semesters, "
                    f"{summary.get('subjects_created', 0)} subjects, "
                    f"{summary.get('components_created', 0)} marks components."
                )
            else:
                messages.error(request, "Import failed. Check the import history for details.")

        except Exception as e:
            messages.error(request, f"A critical error occurred during import: {str(e)}")
        finally:
            # Cleanup
            if fs.exists(filename):
                fs.delete(filename)
            for key in ['academic_import_file', 'academic_import_original_name', 'academic_import_ay_id']:
                request.session.pop(key, None)

        return redirect('academic:year_detail', pk=pk)


# ═══════════════════════════════════════════════
# SEMESTER DETAIL
# ═══════════════════════════════════════════════

class SemesterDetailView(ExamCoordinatorRequiredMixin, DetailView):
    """View subjects and their marks components for a semester."""
    model = Semester
    template_name = 'academic/semester_detail.html'
    context_object_name = 'semester'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        semester = self.object

        # Get all subjects with their components
        subjects = SemesterSubject.objects.filter(
            semester=semester
        ).prefetch_related('marks_components').order_by('subject_code')

        # Collect all unique component names for table header
        all_component_names = []
        for ss in subjects:
            for mc in ss.marks_components.all():
                if mc.name not in all_component_names:
                    all_component_names.append(mc.name)

        # Build subject rows with component values
        subject_rows = []
        for ss in subjects:
            comp_map = {mc.slug: mc.max_marks for mc in ss.marks_components.all()}
            comp_name_map = {mc.name: mc.max_marks for mc in ss.marks_components.all()}
            subject_rows.append({
                'subject': ss,
                'components': comp_name_map,
                'total': ss.total_max_marks,
            })

        ctx.update({
            'academic_year': semester.academic_year,
            'subjects': subject_rows,
            'component_names': all_component_names,
            'breadcrumbs': [
                {'label': 'Academic Years', 'url': reverse('academic:year_list')},
                {'label': semester.academic_year.name, 'url': reverse('academic:year_detail', kwargs={'pk': semester.academic_year.pk})},
                {'label': semester.name, 'url': None},
            ],
        })
        return ctx


# ═══════════════════════════════════════════════
# API ENDPOINTS (for cascading dropdowns)
# ═══════════════════════════════════════════════

class SemesterListAPIView(ExamCoordinatorRequiredMixin, View):
    """JSON endpoint: returns semesters for a given Academic Year."""

    def get(self, request, pk):
        semesters = Semester.objects.filter(
            academic_year_id=pk
        ).order_by('number').values('id', 'number', 'name')

        return JsonResponse({'semesters': list(semesters)})


class SemesterSubjectsAPIView(ExamCoordinatorRequiredMixin, View):
    """JSON endpoint: returns subjects and components for a given Semester."""

    def get(self, request, pk):
        subjects = SemesterSubject.objects.filter(
            semester_id=pk
        ).prefetch_related('marks_components').order_by('subject_code')

        data = []
        for ss in subjects:
            components = [{
                'name': mc.name,
                'slug': mc.slug,
                'max_marks': mc.max_marks,
            } for mc in ss.marks_components.all()]

            data.append({
                'id': ss.id,
                'subject_id': ss.subject_id,
                'code': ss.subject_code,
                'name': ss.subject_name,
                'total_marks': ss.total_max_marks,
                'components': components,
            })

        return JsonResponse({'subjects': data})
