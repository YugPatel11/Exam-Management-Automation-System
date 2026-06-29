"""
Views for Faculty Master & Teaching Allocation Management.

Provides:
- Faculty Master: list, edit, delete, import wizard (upload → preview → confirm)
- Teaching Allocation: list, edit, delete, import wizard
- API: faculty for a subject (for exam auto-fill)

All views are scoped to a specific Academic Year (pk in URL).
"""
import os
import uuid
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.urls import reverse, reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView, UpdateView, DeleteView, View
from django.db.models import Q, Count

from apps.core.mixins import ExamCoordinatorRequiredMixin
from apps.academic.models import (
    AcademicYear, Semester, SemesterSubject,
    FacultyMaster, FacultyTeachingAssignment, FacultyImportLog,
)
from apps.academic.forms import (
    FacultyMasterUploadForm, FacultyMasterEditForm,
    TeachingAllocationUploadForm,
)
from apps.academic.faculty_services import (
    FacultyMasterImportService,
    TeachingAllocationImportService,
)


# ═══════════════════════════════════════════════════════
# FACULTY MASTER — LIST / EDIT / DELETE
# ═══════════════════════════════════════════════════════

class FacultyMasterListView(ExamCoordinatorRequiredMixin, View):
    """List all faculty in the selected Academic Year with search & filters."""

    def get(self, request, pk):
        academic_year = get_object_or_404(AcademicYear, pk=pk)

        qs = FacultyMaster.objects.filter(academic_year=academic_year)

        # Search
        q = request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(faculty_name__icontains=q) |
                Q(short_form__icontains=q) |
                Q(email__icontains=q) |
                Q(department__icontains=q)
            )

        # Filter by status
        status = request.GET.get('status')
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)

        # Filter by department
        dept = request.GET.get('department', '').strip()
        if dept:
            qs = qs.filter(department__iexact=dept)

        # Get unique departments for filter dropdown
        departments = FacultyMaster.objects.filter(
            academic_year=academic_year
        ).exclude(department='').values_list(
            'department', flat=True
        ).distinct().order_by('department')

        # Import history
        import_logs = FacultyImportLog.objects.filter(
            academic_year=academic_year,
            import_type=FacultyImportLog.ImportType.FACULTY_MASTER,
        ).order_by('-created_at')[:5]

        context = {
            'academic_year': academic_year,
            'faculty_list': qs.order_by('faculty_name'),
            'total_faculty': qs.count(),
            'search_query': q,
            'current_status': status or '',
            'current_department': dept,
            'departments': departments,
            'import_logs': import_logs,
            'breadcrumbs': [
                {'label': 'Academic Years', 'url': reverse('academic:year_list')},
                {'label': academic_year.name, 'url': reverse('academic:year_detail', kwargs={'pk': pk})},
                {'label': 'Faculty Master', 'url': None},
            ],
        }
        return render(request, 'academic/faculty_master_list.html', context)


class FacultyMasterEditView(ExamCoordinatorRequiredMixin, UpdateView):
    """Edit a single FacultyMaster record."""
    model = FacultyMaster
    form_class = FacultyMasterEditForm
    template_name = 'academic/faculty_master_form.html'
    pk_url_kwarg = 'fac_pk'

    def get_success_url(self):
        return reverse('academic:faculty_list', kwargs={'pk': self.object.academic_year.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ay = self.object.academic_year
        ctx['academic_year'] = ay
        ctx['title'] = f'Edit Faculty: {self.object.faculty_name}'
        ctx['breadcrumbs'] = [
            {'label': 'Academic Years', 'url': reverse('academic:year_list')},
            {'label': ay.name, 'url': reverse('academic:year_detail', kwargs={'pk': ay.pk})},
            {'label': 'Faculty Master', 'url': reverse('academic:faculty_list', kwargs={'pk': ay.pk})},
            {'label': 'Edit', 'url': None},
        ]
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f"Faculty '{form.instance.faculty_name}' updated.")
        return super().form_valid(form)


class FacultyMasterDeleteView(ExamCoordinatorRequiredMixin, DeleteView):
    """Delete a FacultyMaster record."""
    model = FacultyMaster
    template_name = 'master_data/confirm_delete.html'
    pk_url_kwarg = 'fac_pk'

    def get_success_url(self):
        return reverse('academic:faculty_list', kwargs={'pk': self.kwargs['pk']})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Delete Faculty'
        ctx['cancel_url'] = reverse('academic:faculty_list', kwargs={'pk': self.kwargs['pk']})
        ctx['item_name'] = f"Faculty: {self.object.faculty_name}"
        ctx['warning'] = (
            "This will permanently delete this faculty record and all "
            "associated teaching assignments."
        )
        return ctx

    def form_valid(self, form):
        name = self.object.faculty_name
        response = super().form_valid(form)
        messages.success(self.request, f"Faculty '{name}' deleted.")
        return response


# ═══════════════════════════════════════════════════════
# FACULTY MASTER — IMPORT WIZARD
# ═══════════════════════════════════════════════════════

class FacultyMasterImportUploadView(ExamCoordinatorRequiredMixin, View):
    """Step 1: Upload the faculty list file."""

    def get(self, request, pk):
        academic_year = get_object_or_404(AcademicYear, pk=pk)
        form = FacultyMasterUploadForm()
        existing_count = FacultyMaster.objects.filter(academic_year=academic_year).count()

        context = {
            'step': 1,
            'academic_year': academic_year,
            'form': form,
            'existing_count': existing_count,
            'import_type': 'faculty_master',
            'breadcrumbs': [
                {'label': 'Academic Years', 'url': reverse('academic:year_list')},
                {'label': academic_year.name, 'url': reverse('academic:year_detail', kwargs={'pk': pk})},
                {'label': 'Import Faculty', 'url': None},
            ],
        }
        return render(request, 'academic/faculty_import_wizard.html', context)

    def post(self, request, pk):
        academic_year = get_object_or_404(AcademicYear, pk=pk)
        form = FacultyMasterUploadForm(request.POST, request.FILES)

        if form.is_valid():
            uploaded_file = form.cleaned_data['faculty_file']
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_imports'))
            ext = os.path.splitext(uploaded_file.name)[1]
            temp_name = fs.save(f"faculty_master_{uuid.uuid4().hex}{ext}", uploaded_file)

            request.session['faculty_import_file'] = temp_name
            request.session['faculty_import_original_name'] = uploaded_file.name
            request.session['faculty_import_ay_id'] = str(pk)

            return redirect('academic:faculty_import_preview', pk=pk)

        context = {
            'step': 1,
            'academic_year': academic_year,
            'form': form,
            'import_type': 'faculty_master',
            'breadcrumbs': [
                {'label': 'Academic Years', 'url': reverse('academic:year_list')},
                {'label': academic_year.name, 'url': reverse('academic:year_detail', kwargs={'pk': pk})},
                {'label': 'Import Faculty', 'url': None},
            ],
        }
        return render(request, 'academic/faculty_import_wizard.html', context)


class FacultyMasterImportPreviewView(ExamCoordinatorRequiredMixin, View):
    """Step 2: Preview validation results."""

    def get(self, request, pk):
        academic_year = get_object_or_404(AcademicYear, pk=pk)

        filename = request.session.get('faculty_import_file')
        original_name = request.session.get('faculty_import_original_name', 'unknown')

        if not filename:
            messages.error(request, "No import file found. Please start over.")
            return redirect('academic:faculty_import_upload', pk=pk)

        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_imports'))
        if not fs.exists(filename):
            messages.error(request, "Import file expired or missing. Please start over.")
            return redirect('academic:faculty_import_upload', pk=pk)

        with fs.open(filename, 'rb') as f:
            service = FacultyMasterImportService(f, original_name, academic_year)
            summary = service.validate()

        context = {
            'step': 2,
            'academic_year': academic_year,
            'summary': summary,
            'filename': filename,
            'original_name': original_name,
            'import_type': 'faculty_master',
            'breadcrumbs': [
                {'label': 'Academic Years', 'url': reverse('academic:year_list')},
                {'label': academic_year.name, 'url': reverse('academic:year_detail', kwargs={'pk': pk})},
                {'label': 'Import Faculty — Preview', 'url': None},
            ],
        }
        return render(request, 'academic/faculty_import_wizard.html', context)


class FacultyMasterImportProcessView(ExamCoordinatorRequiredMixin, View):
    """Step 3: Confirm and commit."""

    def post(self, request, pk):
        academic_year = get_object_or_404(AcademicYear, pk=pk)

        filename = request.session.get('faculty_import_file')
        original_name = request.session.get('faculty_import_original_name', 'unknown')

        if not filename:
            messages.error(request, "No import session found.")
            return redirect('academic:faculty_import_upload', pk=pk)

        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_imports'))
        if not fs.exists(filename):
            messages.error(request, "Import file missing. Please start over.")
            return redirect('academic:faculty_import_upload', pk=pk)

        try:
            with fs.open(filename, 'rb') as f:
                service = FacultyMasterImportService(f, original_name, academic_year)
                service.validate()
                import_log = service.process_import(imported_by=request.user)

            if import_log.status == FacultyImportLog.ImportStatus.SUCCESS:
                s = import_log.summary
                messages.success(
                    request,
                    f"Faculty import successful! "
                    f"{s.get('records_created', 0)} created, "
                    f"{s.get('records_updated', 0)} updated."
                )
            else:
                messages.error(request, "Import failed. Check import history for details.")

        except Exception as e:
            messages.error(request, f"Critical error during import: {str(e)}")
        finally:
            if fs.exists(filename):
                fs.delete(filename)
            for key in ['faculty_import_file', 'faculty_import_original_name', 'faculty_import_ay_id']:
                request.session.pop(key, None)

        return redirect('academic:faculty_list', pk=pk)


# ═══════════════════════════════════════════════════════
# TEACHING ALLOCATION — LIST / EDIT / DELETE
# ═══════════════════════════════════════════════════════

class TeachingAllocationListView(ExamCoordinatorRequiredMixin, View):
    """List all teaching assignments for an Academic Year with rich filtering."""

    def get(self, request, pk):
        academic_year = get_object_or_404(AcademicYear, pk=pk)

        qs = FacultyTeachingAssignment.objects.filter(
            academic_year=academic_year
        ).select_related('semester', 'semester_subject', 'faculty')

        # Filters
        q = request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(semester_subject__subject_code__icontains=q) |
                Q(semester_subject__subject_name__icontains=q) |
                Q(class_name__icontains=q) |
                Q(faculty__faculty_name__icontains=q) |
                Q(faculty__short_form__icontains=q) |
                Q(faculty_alias_raw__icontains=q)
            )

        sem_filter = request.GET.get('semester', '').strip()
        if sem_filter:
            qs = qs.filter(semester_id=sem_filter)

        class_filter = request.GET.get('class_name', '').strip()
        if class_filter:
            qs = qs.filter(class_name=class_filter)

        faculty_filter = request.GET.get('faculty', '').strip()
        if faculty_filter:
            qs = qs.filter(faculty_id=faculty_filter)

        type_filter = request.GET.get('teaching_type', '').strip()
        if type_filter:
            qs = qs.filter(teaching_type=type_filter)

        # Get filter options
        semesters = Semester.objects.filter(
            academic_year=academic_year
        ).order_by('number')

        classes = FacultyTeachingAssignment.objects.filter(
            academic_year=academic_year
        ).values_list('class_name', flat=True).distinct().order_by('class_name')

        faculty_options = FacultyMaster.objects.filter(
            academic_year=academic_year,
            is_active=True
        ).order_by('faculty_name')

        # Import history
        import_logs = FacultyImportLog.objects.filter(
            academic_year=academic_year,
            import_type=FacultyImportLog.ImportType.TEACHING_ALLOCATION,
        ).order_by('-created_at')[:5]

        context = {
            'academic_year': academic_year,
            'assignments': qs.order_by('semester__number', 'class_name', 'semester_subject__subject_code'),
            'total_assignments': qs.count(),
            'search_query': q,
            'semesters': semesters,
            'classes': classes,
            'faculty_options': faculty_options,
            'teaching_types': FacultyTeachingAssignment.TeachingType.choices,
            'current_semester': sem_filter,
            'current_class': class_filter,
            'current_faculty': faculty_filter,
            'current_type': type_filter,
            'import_logs': import_logs,
            'has_faculty_master': FacultyMaster.objects.filter(academic_year=academic_year).exists(),
            'breadcrumbs': [
                {'label': 'Academic Years', 'url': reverse('academic:year_list')},
                {'label': academic_year.name, 'url': reverse('academic:year_detail', kwargs={'pk': pk})},
                {'label': 'Teaching Allocation', 'url': None},
            ],
        }
        return render(request, 'academic/allocation_list.html', context)


class TeachingAllocationDeleteView(ExamCoordinatorRequiredMixin, DeleteView):
    """Delete a teaching assignment."""
    model = FacultyTeachingAssignment
    template_name = 'master_data/confirm_delete.html'
    pk_url_kwarg = 'alloc_pk'

    def get_success_url(self):
        return reverse('academic:allocation_list', kwargs={'pk': self.kwargs['pk']})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Delete Teaching Assignment'
        ctx['cancel_url'] = reverse('academic:allocation_list', kwargs={'pk': self.kwargs['pk']})
        ctx['item_name'] = str(self.object)
        ctx['warning'] = "This will permanently delete this teaching assignment."
        return ctx

    def form_valid(self, form):
        desc = str(self.object)
        response = super().form_valid(form)
        messages.success(self.request, f"Assignment deleted: {desc}")
        return response


# ═══════════════════════════════════════════════════════
# TEACHING ALLOCATION — IMPORT WIZARD
# ═══════════════════════════════════════════════════════

class AllocationImportUploadView(ExamCoordinatorRequiredMixin, View):
    """Step 1: Upload allocation file."""

    def get(self, request, pk):
        academic_year = get_object_or_404(AcademicYear, pk=pk)
        form = TeachingAllocationUploadForm()
        existing_count = FacultyTeachingAssignment.objects.filter(academic_year=academic_year).count()
        has_faculty = FacultyMaster.objects.filter(academic_year=academic_year).exists()
        has_structure = Semester.objects.filter(academic_year=academic_year).exists()

        context = {
            'step': 1,
            'academic_year': academic_year,
            'form': form,
            'existing_count': existing_count,
            'has_faculty_master': has_faculty,
            'has_academic_structure': has_structure,
            'import_type': 'teaching_allocation',
            'breadcrumbs': [
                {'label': 'Academic Years', 'url': reverse('academic:year_list')},
                {'label': academic_year.name, 'url': reverse('academic:year_detail', kwargs={'pk': pk})},
                {'label': 'Import Teaching Allocation', 'url': None},
            ],
        }
        return render(request, 'academic/allocation_import_wizard.html', context)

    def post(self, request, pk):
        academic_year = get_object_or_404(AcademicYear, pk=pk)
        form = TeachingAllocationUploadForm(request.POST, request.FILES)

        if form.is_valid():
            uploaded_file = form.cleaned_data['allocation_file']
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_imports'))
            ext = os.path.splitext(uploaded_file.name)[1]
            temp_name = fs.save(f"allocation_{uuid.uuid4().hex}{ext}", uploaded_file)

            request.session['allocation_import_file'] = temp_name
            request.session['allocation_import_original_name'] = uploaded_file.name
            request.session['allocation_import_ay_id'] = str(pk)

            return redirect('academic:allocation_import_preview', pk=pk)

        context = {
            'step': 1,
            'academic_year': academic_year,
            'form': form,
            'import_type': 'teaching_allocation',
            'breadcrumbs': [
                {'label': 'Academic Years', 'url': reverse('academic:year_list')},
                {'label': academic_year.name, 'url': reverse('academic:year_detail', kwargs={'pk': pk})},
                {'label': 'Import Teaching Allocation', 'url': None},
            ],
        }
        return render(request, 'academic/allocation_import_wizard.html', context)


class AllocationImportPreviewView(ExamCoordinatorRequiredMixin, View):
    """Step 2: Preview validation results."""

    def get(self, request, pk):
        academic_year = get_object_or_404(AcademicYear, pk=pk)

        filename = request.session.get('allocation_import_file')
        original_name = request.session.get('allocation_import_original_name', 'unknown')

        if not filename:
            messages.error(request, "No import file found. Please start over.")
            return redirect('academic:allocation_import_upload', pk=pk)

        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_imports'))
        if not fs.exists(filename):
            messages.error(request, "Import file expired. Please start over.")
            return redirect('academic:allocation_import_upload', pk=pk)

        with fs.open(filename, 'rb') as f:
            service = TeachingAllocationImportService(f, original_name, academic_year)
            summary = service.validate()

        context = {
            'step': 2,
            'academic_year': academic_year,
            'summary': summary,
            'filename': filename,
            'original_name': original_name,
            'import_type': 'teaching_allocation',
            'breadcrumbs': [
                {'label': 'Academic Years', 'url': reverse('academic:year_list')},
                {'label': academic_year.name, 'url': reverse('academic:year_detail', kwargs={'pk': pk})},
                {'label': 'Import Allocation — Preview', 'url': None},
            ],
        }
        return render(request, 'academic/allocation_import_wizard.html', context)


class AllocationImportProcessView(ExamCoordinatorRequiredMixin, View):
    """Step 3: Confirm and commit."""

    def post(self, request, pk):
        academic_year = get_object_or_404(AcademicYear, pk=pk)

        filename = request.session.get('allocation_import_file')
        original_name = request.session.get('allocation_import_original_name', 'unknown')

        if not filename:
            messages.error(request, "No import session found.")
            return redirect('academic:allocation_import_upload', pk=pk)

        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_imports'))
        if not fs.exists(filename):
            messages.error(request, "Import file missing. Please start over.")
            return redirect('academic:allocation_import_upload', pk=pk)

        try:
            with fs.open(filename, 'rb') as f:
                service = TeachingAllocationImportService(f, original_name, academic_year)
                service.validate()
                import_log = service.process_import(imported_by=request.user)

            if import_log.status == FacultyImportLog.ImportStatus.SUCCESS:
                s = import_log.summary
                messages.success(
                    request,
                    f"Teaching allocation import successful! "
                    f"{s.get('assignments_created', 0)} created, "
                    f"{s.get('assignments_updated', 0)} updated."
                )
            else:
                messages.error(request, "Import failed. Check import history.")

        except Exception as e:
            messages.error(request, f"Critical error: {str(e)}")
        finally:
            if fs.exists(filename):
                fs.delete(filename)
            for key in ['allocation_import_file', 'allocation_import_original_name', 'allocation_import_ay_id']:
                request.session.pop(key, None)

        return redirect('academic:allocation_list', pk=pk)


# ═══════════════════════════════════════════════════════
# API — Faculty for Subject (for exam auto-fill)
# ═══════════════════════════════════════════════════════

class SubjectFacultyAPIView(ExamCoordinatorRequiredMixin, View):
    """JSON endpoint: returns assigned faculty for a given SemesterSubject."""

    def get(self, request, pk, ss_pk):
        assignments = FacultyTeachingAssignment.objects.filter(
            semester_subject_id=ss_pk,
            academic_year_id=pk,
        ).select_related('faculty').order_by('class_name', 'teaching_type')

        data = []
        for a in assignments:
            data.append({
                'id': a.id,
                'class_name': a.class_name,
                'teaching_type': a.teaching_type,
                'teaching_type_display': a.get_teaching_type_display(),
                'is_coordinator': a.is_coordinator,
                'faculty_id': a.faculty_id,
                'faculty_name': a.faculty.faculty_name if a.faculty else a.faculty_alias_raw,
                'faculty_email': a.faculty.email if a.faculty else '',
                'faculty_alias': a.faculty.short_form if a.faculty else a.faculty_alias_raw,
            })

        return JsonResponse({'assignments': data})
