"""
Views for Marks Management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, View, DetailView
from django.db import transaction

from apps.core.mixins import ExamCoordinatorRequiredMixin, FacultyRequiredMixin
from apps.exams.models import Exam
from apps.marks.models import MarksEntryTask, StudentMark
from apps.marks.services import MarksAllocationService, MarksCsvImportService
from apps.marks.forms import DynamicMarksEntryForm, CsvUploadForm
from apps.students.models import Student
from apps.curriculum.models import CurriculumMapping


# ==========================================
# COORDINATOR VIEWS (Allocation & Review)
# ==========================================

class MarksAllocationDashboardView(ExamCoordinatorRequiredMixin, ListView):
    """
    List of Exams for Exam Coordinators to manage marks allocation.
    """
    model = Exam
    template_name = 'marks/allocation_dashboard.html'
    context_object_name = 'exams'


class MarksAllocationManagerView(ExamCoordinatorRequiredMixin, View):
    """
    Allocates and manages Marks Entry Tasks for a specific Exam.
    """
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        tasks = MarksEntryTask.objects.filter(exam=exam).select_related('subject', 'division', 'faculty')
        
        context = {
            'exam': exam,
            'tasks': tasks,
            'total_tasks': tasks.count(),
        }
        return render(request, 'marks/allocation_manager.html', context)

    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        action = request.POST.get('action')
        
        if action == 'auto_allocate':
            service = MarksAllocationService(exam=exam)
            success = service.allocate()
            
            if service.errors:
                for err in service.errors:
                    messages.error(request, err)
            elif success:
                messages.success(request, f"Successfully allocated {service.allocated_count} marks entry tasks.")
                
        return redirect('marks:allocation_manager', exam_id=exam.id)


class MarksReviewDashboardView(ExamCoordinatorRequiredMixin, ListView):
    """
    List of Marks Entry Tasks for review.
    """
    model = MarksEntryTask
    template_name = 'marks/review_dashboard.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        return MarksEntryTask.objects.all().select_related('exam', 'subject', 'division', 'faculty').order_by('-created_at')


class MarksReviewDetailView(ExamCoordinatorRequiredMixin, View):
    """
    Review a specific Marks Entry Task, view marks, and lock/unlock.
    """
    def get(self, request, pk):
        task = get_object_or_404(MarksEntryTask, pk=pk)
        marks = StudentMark.objects.filter(task=task).select_related('student')
        
        # Get components dynamically from the task
        comp_data = task.get_marks_components()
        components = comp_data.get('fields', [])
            
        context = {
            'task': task,
            'marks': marks,
            'components': components,
            'comp_data': comp_data,
        }
        return render(request, 'marks/review_detail.html', context)
        
    def post(self, request, pk):
        task = get_object_or_404(MarksEntryTask, pk=pk)
        action = request.POST.get('action')
        
        if action == 'lock':
            if task.status == 'submitted':
                task.status = 'locked'
                task.save()
                messages.success(request, "Marks locked successfully.")
            else:
                messages.error(request, "Task must be submitted before locking.")
                
        elif action == 'unlock':
            if task.status == 'locked':
                task.status = 'in_progress'
                task.save()
                messages.success(request, "Marks unlocked and sent back to faculty.")
                
        elif action == 'return':
            if task.status == 'submitted':
                task.status = 'in_progress'
                task.save()
                messages.success(request, "Task returned to faculty for changes.")
                
        return redirect('marks:review_detail', pk=task.pk)


# ==========================================
# FACULTY VIEWS (Entry & Submission)
# ==========================================

class MarksEntryListView(FacultyRequiredMixin, ListView):
    """
    List of Marks Entry Tasks assigned to the logged-in faculty.
    """
    model = MarksEntryTask
    template_name = 'marks/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        return MarksEntryTask.objects.filter(faculty=self.request.user).select_related('exam', 'subject', 'division')


class MarksEntryFormView(FacultyRequiredMixin, View):
    """
    Dynamic form to enter marks for a specific task.
    """
    def _get_comp_data(self, task):
        """Get marks components dict from the task."""
        return task.get_marks_components()
        
    def get(self, request, pk):
        task = get_object_or_404(MarksEntryTask, pk=pk, faculty=request.user)
        
        is_read_only = False
        if task.status in ['submitted', 'locked']:
            messages.info(request, f"This task is {task.status}. Marks are view-only.")
            is_read_only = True

        # Check marks entry window
        from django.utils import timezone
        now = timezone.now()
        exam = task.exam
        if exam.marks_entry_start and now < exam.marks_entry_start:
            messages.error(request, f"Marks entry has not started yet. It opens on {exam.marks_entry_start.strftime('%d %b %Y, %I:%M %p')}.")
            return redirect('marks:task_list')
            
        if not is_read_only and exam.marks_entry_end and now > exam.marks_entry_end:
            messages.warning(request, f"Marks entry window has closed. Marks are view-only.")
            is_read_only = True
            
        comp_data = self._get_comp_data(task)
        components = comp_data.get('fields', [])
        use_theory_ce_formula = comp_data.get('use_theory_ce_formula', False)
        
        # Get students for this task
        if task.teaching_assignment:
            qs = Student.objects.filter(
                academic_year=task.teaching_assignment.academic_year,
                class_name=task.teaching_assignment.class_name
            )
            # Filter by batch if it's a practical batch
            t_type = task.teaching_assignment.teaching_type
            if t_type == 'practical_batch_a':
                qs = qs.filter(batch='A')
            elif t_type == 'practical_batch_b':
                qs = qs.filter(batch='B')
            elif t_type == 'practical_batch_c':
                qs = qs.filter(batch='C')
            
            students = list(qs.order_by('enrollment_no'))
        else:
            # Legacy fallback
            mappings = CurriculumMapping.objects.filter(subject=task.subject)
            students_qs = Student.objects.none()
            for m in mappings:
                qs = Student.objects.filter(program=m.program, semester=m.semester)
                if task.division:
                    qs = qs.filter(division=task.division)
                students_qs = students_qs | qs
                
            students = list(students_qs.distinct().order_by('roll_no'))
        
        # Prepare forms
        student_forms = []
        for student in students:
            # Get existing mark or create
            mark, _ = StudentMark.objects.get_or_create(task=task, student=student)
            prefix = f'student_{student.id}'
            form = DynamicMarksEntryForm(
                instance=mark, prefix=prefix,
                components=components,
                use_theory_ce_formula=use_theory_ce_formula
            )
            student_forms.append({
                'student': student,
                'form': form
            })
            
        context = {
            'task': task,
            'components': components,
            'comp_data': comp_data,
            'student_forms': student_forms,
            'is_read_only': is_read_only,
        }
        return render(request, 'marks/entry_form.html', context)
        
    def post(self, request, pk):
        task = get_object_or_404(MarksEntryTask, pk=pk, faculty=request.user)
        
        if task.status in ['submitted', 'locked']:
            messages.error(request, "Task is already submitted or locked.")
            return redirect('marks:task_list')

        # Check marks entry window
        from django.utils import timezone
        now = timezone.now()
        exam = task.exam
        if exam.marks_entry_start and now < exam.marks_entry_start:
            messages.error(request, "Marks entry has not started yet.")
            return redirect('marks:task_list')
        if exam.marks_entry_end and now > exam.marks_entry_end:
            messages.error(request, "Marks entry window has closed.")
            return redirect('marks:task_list')

        comp_data = self._get_comp_data(task)
        components = comp_data.get('fields', [])
        use_theory_ce_formula = comp_data.get('use_theory_ce_formula', False)
        
        action = request.POST.get('action')
        
        # Process all forms
        marks_qs = StudentMark.objects.filter(task=task)
        
        all_valid = True
        with transaction.atomic():
            for mark in marks_qs:
                prefix = f'student_{mark.student.id}'
                form = DynamicMarksEntryForm(
                    request.POST, instance=mark, prefix=prefix,
                    components=components,
                    use_theory_ce_formula=use_theory_ce_formula
                )
                if form.is_valid():
                    form.save()
                else:
                    all_valid = False
                    
            if all_valid:
                if action == 'submit':
                    task.status = 'submitted'
                    messages.success(request, "Marks submitted for review.")
                else:
                    task.status = 'in_progress'
                    messages.success(request, "Marks saved as draft.")
                task.save()
                return redirect('marks:task_list')
            else:
                messages.error(request, "Please correct the errors in the form.")
                return redirect('marks:entry_form', pk=task.pk)


class MarksCsvUploadView(FacultyRequiredMixin, View):
    """
    Handle CSV upload for marks entry.
    """
    def post(self, request, pk):
        task = get_object_or_404(MarksEntryTask, pk=pk, faculty=request.user)
        
        if task.status in ['submitted', 'locked']:
            messages.error(request, "Task is already submitted or locked.")
            return redirect('marks:task_list')
            
        form = CsvUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data['file']
            
            # Get components dynamically from the task
            comp_data = task.get_marks_components()
            components = comp_data.get('fields', [])
            use_theory_ce_formula = comp_data.get('use_theory_ce_formula', False)
            
            service = MarksCsvImportService(
                task=task, components=components,
                use_theory_ce_formula=use_theory_ce_formula
            )
            success = service.process(csv_file)
            
            if success:
                messages.success(request, f"Successfully imported marks for {service.success_count} students.")
            else:
                for err in service.errors:
                    messages.error(request, err)
                    
        return redirect('marks:entry_form', pk=task.pk)

import csv
from django.http import HttpResponse

class MarksCsvSampleView(FacultyRequiredMixin, View):
    """
    Generate a dynamic sample CSV with correct headers for the task.
    """
    def get(self, request, pk):
        task = get_object_or_404(MarksEntryTask, pk=pk, faculty=request.user)
        comp_data = task.get_marks_components()
        components = comp_data.get('fields', [])
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="sample_marks_{task.subject.code}.csv"'
        
        writer = csv.writer(response)
        
        # Write headers
        headers = ['RollNo', 'Status']
        for comp in components:
            headers.append(comp['key'])
        headers.append('Total')
        writer.writerow(headers)
        
        # Write sample rows with actual max_marks as sample values
        row1_marks = [comp.get('max_marks', 5) or 5 for comp in components]
        
        # Get students for this task
        if task.teaching_assignment:
            from apps.students.models import Student
            qs = Student.objects.filter(
                academic_year=task.teaching_assignment.academic_year,
                class_name=task.teaching_assignment.class_name
            )
            t_type = task.teaching_assignment.teaching_type
            if t_type == 'practical_batch_a':
                qs = qs.filter(batch='A')
            elif t_type == 'practical_batch_b':
                qs = qs.filter(batch='B')
            elif t_type == 'practical_batch_c':
                qs = qs.filter(batch='C')
            students = list(qs.order_by('enrollment_no'))
        else:
            students = [] # Fallback

        # Calculate sample total
        if comp_data.get('use_theory_ce_formula', False):
            # Group marks by group for formula
            group_totals = {}
            for comp, val in zip(components, row1_marks):
                group = comp.get('group', '')
                group_totals.setdefault(group, 0)
                group_totals[group] += val
            internal_sums = []
            fe_sum = 0
            counted = set()
            for comp in components:
                group = comp.get('group', '')
                if group in counted:
                    continue
                counted.add(group)
                g_lower = group.lower()
                g_val = group_totals.get(group, 0)
                if 'internal' in g_lower or 'exam' in g_lower or 'theory' in g_lower:
                    internal_sums.append(g_val)
                else:
                    fe_sum += g_val
            if len(internal_sums) >= 2:
                sample_total = sum(internal_sums) / len(internal_sums) + fe_sum
            else:
                sample_total = sum(row1_marks)
        else:
            sample_total = sum(row1_marks)
            
        sample_rows = []
        if students:
            for s in students:
                sample_rows.append([s.roll_no, 'Present'] + row1_marks + [sample_total])
        else:
            sample_rows.append(['101', 'Present'] + row1_marks + [sample_total])
            
        writer.writerows(sample_rows)
        return response
