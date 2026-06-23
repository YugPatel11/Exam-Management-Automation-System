"""
Views for Faculty Assignments Management.
"""
import os
import uuid
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.urls import reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import ListView, FormView, View
from django.db.models import Q, Prefetch

from apps.core.mixins import ExamCoordinatorRequiredMixin
from apps.master_data.models import Subject
from apps.faculty.models import SubjectCoordinatorAssignment, SubjectFacultyAssignment
from apps.faculty.forms import AssignmentUploadForm
from apps.faculty.services import CoordinatorImportService, FacultyImportService


class AssignmentListView(ExamCoordinatorRequiredMixin, ListView):
    """
    List view for displaying Subjects along with their assigned Coordinators and Faculty.
    We base it on the Subject model to group assignments neatly.
    """
    model = Subject
    template_name = 'faculty/assignment_list.html'
    context_object_name = 'subjects'
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset().prefetch_related(
            Prefetch('coordinator_assignments', queryset=SubjectCoordinatorAssignment.objects.select_related('coordinator')),
            Prefetch('faculty_assignments', queryset=SubjectFacultyAssignment.objects.select_related('faculty'))
        )
        
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(
                Q(code__icontains=query) | 
                Q(name__icontains=query)
            ).distinct()
            
        return qs


# --- COORDINATOR IMPORT WIZARD ---

class CoordinatorImportWizardView(ExamCoordinatorRequiredMixin, FormView):
    template_name = 'faculty/import_wizard.html'
    form_class = AssignmentUploadForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['step'] = 1
        ctx['import_type'] = 'coordinator'
        ctx['import_title'] = 'Subject Coordinator Import'
        return ctx

    def form_valid(self, form):
        csv_file = form.cleaned_data['csv_file']
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_imports'))
        filename = fs.save(f"coordinator_import_{uuid.uuid4().hex}.csv", csv_file)
        self.request.session['coordinator_import_file'] = filename
        return redirect('faculty:coordinator_import_preview')


class CoordinatorImportPreviewView(ExamCoordinatorRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        filename = request.session.get('coordinator_import_file')
        if not filename:
            messages.error(request, "No import file found.")
            return redirect('faculty:coordinator_import_wizard')

        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_imports'))
        if not fs.exists(filename):
            messages.error(request, "File expired.")
            return redirect('faculty:coordinator_import_wizard')

        with fs.open(filename, 'rb') as f:
            service = CoordinatorImportService(f)
            summary = service.validate_file()

        context = {
            'step': 2,
            'import_type': 'coordinator',
            'import_title': 'Subject Coordinator Import',
            'summary': summary,
        }
        return render(request, 'faculty/import_wizard.html', context)


class CoordinatorImportProcessView(ExamCoordinatorRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        filename = request.session.get('coordinator_import_file')
        if not filename:
            return redirect('faculty:coordinator_import_wizard')

        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_imports'))
        try:
            with fs.open(filename, 'rb') as f:
                service = CoordinatorImportService(f)
                service.validate_file()
                created = service.process_import()
                
            messages.success(request, f"Import complete: {created} new Coordinator Assignments created.")
        except Exception as e:
            messages.error(request, f"Error during import: {str(e)}")
        finally:
            if fs.exists(filename):
                fs.delete(filename)
            if 'coordinator_import_file' in request.session:
                del request.session['coordinator_import_file']

        return redirect('faculty:assignment_list')


# --- FACULTY IMPORT WIZARD ---

class FacultyImportWizardView(ExamCoordinatorRequiredMixin, FormView):
    template_name = 'faculty/import_wizard.html'
    form_class = AssignmentUploadForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['step'] = 1
        ctx['import_type'] = 'faculty'
        ctx['import_title'] = 'Subject Faculty Import'
        return ctx

    def form_valid(self, form):
        csv_file = form.cleaned_data['csv_file']
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_imports'))
        filename = fs.save(f"faculty_import_{uuid.uuid4().hex}.csv", csv_file)
        self.request.session['faculty_import_file'] = filename
        return redirect('faculty:faculty_import_preview')


class FacultyImportPreviewView(ExamCoordinatorRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        filename = request.session.get('faculty_import_file')
        if not filename:
            messages.error(request, "No import file found.")
            return redirect('faculty:faculty_import_wizard')

        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_imports'))
        if not fs.exists(filename):
            messages.error(request, "File expired.")
            return redirect('faculty:faculty_import_wizard')

        with fs.open(filename, 'rb') as f:
            service = FacultyImportService(f)
            summary = service.validate_file()

        context = {
            'step': 2,
            'import_type': 'faculty',
            'import_title': 'Subject Faculty Import',
            'summary': summary,
        }
        return render(request, 'faculty/import_wizard.html', context)


class FacultyImportProcessView(ExamCoordinatorRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        filename = request.session.get('faculty_import_file')
        if not filename:
            return redirect('faculty:faculty_import_wizard')

        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_imports'))
        try:
            with fs.open(filename, 'rb') as f:
                service = FacultyImportService(f)
                service.validate_file()
                created = service.process_import()
                
            messages.success(request, f"Import complete: {created} new Subject Faculty Assignments created.")
        except Exception as e:
            messages.error(request, f"Error during import: {str(e)}")
        finally:
            if fs.exists(filename):
                fs.delete(filename)
            if 'faculty_import_file' in request.session:
                del request.session['faculty_import_file']

        return redirect('faculty:assignment_list')
