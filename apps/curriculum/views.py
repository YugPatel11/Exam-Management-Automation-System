"""
Views for Curriculum and Examination Scheme Management.
"""
import os
import uuid
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import ListView, FormView, View
from django.db.models import Q

from apps.core.mixins import ExamCoordinatorRequiredMixin
from apps.curriculum.models import CurriculumMapping, AssessmentScheme
from apps.curriculum.forms import CurriculumUploadForm
from apps.curriculum.services import CurriculumImportService


class CurriculumListView(ExamCoordinatorRequiredMixin, ListView):
    """
    List view for displaying curriculum mappings and their assessment schemes.
    """
    model = CurriculumMapping
    template_name = 'curriculum/scheme_list.html'
    context_object_name = 'mappings'
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset().select_related('subject', 'program', 'subject__assessment_scheme')
        
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(
                Q(subject__code__icontains=query) | 
                Q(subject__name__icontains=query) |
                Q(program__code__icontains=query)
            )
            
        semester = self.request.GET.get('semester')
        if semester:
            qs = qs.filter(semester=semester)
            
        return qs


class ImportWizardView(ExamCoordinatorRequiredMixin, FormView):
    """
    Step 1: Upload the CSV file.
    """
    template_name = 'curriculum/import_wizard.html'
    form_class = CurriculumUploadForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['step'] = 1
        return ctx

    def form_valid(self, form):
        csv_file = form.cleaned_data['csv_file']
        
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_imports'))
        filename = fs.save(f"curriculum_import_{uuid.uuid4().hex}.csv", csv_file)
        
        self.request.session['curriculum_import_file'] = filename
        return redirect('curriculum:import_preview')


class ImportPreviewView(ExamCoordinatorRequiredMixin, View):
    """
    Step 2: Preview the validation results.
    """
    def get(self, request, *args, **kwargs):
        filename = request.session.get('curriculum_import_file')
        if not filename:
            messages.error(request, "No import file found. Please start over.")
            return redirect('curriculum:import_wizard')

        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_imports'))
        if not fs.exists(filename):
            messages.error(request, "Import file expired or missing. Please start over.")
            return redirect('curriculum:import_wizard')

        with fs.open(filename, 'rb') as f:
            service = CurriculumImportService(f)
            summary = service.validate_file()

        context = {
            'step': 2,
            'summary': summary,
            'filename': filename
        }
        return render(request, 'curriculum/import_wizard.html', context)


class ImportProcessView(ExamCoordinatorRequiredMixin, View):
    """
    Step 3: Commit the valid rows to the database.
    """
    def post(self, request, *args, **kwargs):
        filename = request.session.get('curriculum_import_file')
        if not filename:
            messages.error(request, "No import session found.")
            return redirect('curriculum:import_wizard')

        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_imports'))
        if not fs.exists(filename):
            messages.error(request, "Import file missing. Please start over.")
            return redirect('curriculum:import_wizard')

        try:
            with fs.open(filename, 'rb') as f:
                service = CurriculumImportService(f)
                service.validate_file()
                created_mappings, updated_schemes = service.process_import()
                
            messages.success(request, f"Curriculum Import complete: {created_mappings} mappings created, {updated_schemes} schemes created/updated.")
            
        except Exception as e:
            messages.error(request, f"A critical error occurred during import: {str(e)}")
        finally:
            if fs.exists(filename):
                fs.delete(filename)
            if 'curriculum_import_file' in request.session:
                del request.session['curriculum_import_file']

        return redirect('curriculum:scheme_list')
