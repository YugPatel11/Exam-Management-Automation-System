"""
Views for Student Management.
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
from apps.students.models import Student
from apps.students.forms import CSVUploadForm
from apps.students.services import StudentImportService


class StudentListView(ExamCoordinatorRequiredMixin, ListView):
    """
    List view for displaying all students with search and filter functionality.
    """
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset().select_related('program', 'division')
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(
                Q(roll_no__icontains=query) | 
                Q(enrollment_no__icontains=query) | 
                Q(name__icontains=query)
            )
            
        program_id = self.request.GET.get('program')
        if program_id:
            qs = qs.filter(program_id=program_id)
            
        semester = self.request.GET.get('semester')
        if semester:
            qs = qs.filter(semester=semester)
            
        return qs


class ImportWizardView(ExamCoordinatorRequiredMixin, FormView):
    """
    Step 1: Upload the CSV file.
    Saves it temporarily and redirects to the preview step.
    """
    template_name = 'students/import_wizard.html'
    form_class = CSVUploadForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['step'] = 1
        return ctx

    def form_valid(self, form):
        csv_file = form.cleaned_data['csv_file']
        
        # Save file temporarily
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_imports'))
        filename = fs.save(f"student_import_{uuid.uuid4().hex}.csv", csv_file)
        
        # Store filename in session
        self.request.session['import_file'] = filename
        
        return redirect('students:import_preview')


class ImportPreviewView(ExamCoordinatorRequiredMixin, View):
    """
    Step 2: Preview the validation results.
    Reads the temp file, runs validation, shows stats and errors.
    """
    def get(self, request, *args, **kwargs):
        filename = request.session.get('import_file')
        if not filename:
            messages.error(request, "No import file found. Please start over.")
            return redirect('students:import_wizard')

        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_imports'))
        if not fs.exists(filename):
            messages.error(request, "Import file expired or missing. Please start over.")
            return redirect('students:import_wizard')

        # Read and validate
        with fs.open(filename, 'rb') as f:
            service = StudentImportService(f)
            summary = service.validate_file()

        context = {
            'step': 2,
            'summary': summary,
            'filename': filename
        }
        return render(request, 'students/import_wizard.html', context)


class ImportProcessView(ExamCoordinatorRequiredMixin, View):
    """
    Step 3: Commit the valid rows to the database.
    """
    def post(self, request, *args, **kwargs):
        filename = request.session.get('import_file')
        if not filename:
            messages.error(request, "No import session found.")
            return redirect('students:import_wizard')

        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_imports'))
        if not fs.exists(filename):
            messages.error(request, "Import file missing. Please start over.")
            return redirect('students:import_wizard')

        try:
            with fs.open(filename, 'rb') as f:
                service = StudentImportService(f)
                # Must run validate to populate valid_rows
                service.validate_file()
                created, updated = service.process_import()
                
            messages.success(request, f"Import complete: {created} created, {updated} updated.")
            
        except Exception as e:
            messages.error(request, f"A critical error occurred during import: {str(e)}")
        finally:
            # Clean up temp file and session
            if fs.exists(filename):
                fs.delete(filename)
            if 'import_file' in request.session:
                del request.session['import_file']

        return redirect('students:student_list')
