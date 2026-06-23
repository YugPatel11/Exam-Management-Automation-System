"""
Views for Exam Scheduling.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, View
from collections import defaultdict
from itertools import groupby
from operator import attrgetter

from apps.core.mixins import ExamCoordinatorRequiredMixin
from apps.exams.models import Exam
from apps.scheduling.models import ExamSchedule
from apps.scheduling.services import ScheduleGeneratorService
from apps.scheduling.forms import AutoGenerateForm, ExamScheduleEditForm


class ScheduleDashboardView(ExamCoordinatorRequiredMixin, ListView):
    """
    List of Exams for Exam Coordinators to manage their schedules.
    """
    model = Exam
    template_name = 'scheduling/dashboard.html'
    context_object_name = 'exams'

    def get_queryset(self):
        return Exam.objects.all().prefetch_related('schedules', 'programs')


class ScheduleManagerView(ExamCoordinatorRequiredMixin, View):
    """
    Manages the schedule for a specific Exam.
    Provides tabs for Date-wise, Subject-wise, and Program-wise views.
    Handles Auto-Generate, Edit, Lock, and Delete actions.
    """
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        schedules = ExamSchedule.objects.filter(exam=exam).select_related('subject')
        
        # Determine active tab
        active_tab = request.GET.get('tab', 'date')

        # Generate views
        date_wise = defaultdict(list)
        for s in schedules.order_by('date', 'start_time'):
            date_wise[s.date].append(s)
            
        # Program-wise requires looking up CurriculumMappings to see which programs a subject belongs to.
        from apps.curriculum.models import CurriculumMapping
        mappings = CurriculumMapping.objects.filter(
            subject__in=[s.subject for s in schedules]
        ).select_related('program', 'subject')
        
        program_wise = defaultdict(list)
        for m in mappings:
            # Find the schedule for this subject
            sched = next((x for x in schedules if x.subject_id == m.subject_id), None)
            if sched:
                program_wise[m.program].append({
                    'semester': m.semester,
                    'schedule': sched
                })

        context = {
            'exam': exam,
            'schedules': schedules,
            'active_tab': active_tab,
            'date_wise': dict(date_wise),
            'program_wise': dict(program_wise),
            'auto_generate_form': AutoGenerateForm(),
        }
        return render(request, 'scheduling/manager.html', context)

    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        action = request.POST.get('action')

        if action == 'auto_generate':
            form = AutoGenerateForm(request.POST)
            if form.is_valid():
                service = ScheduleGeneratorService(
                    exam=exam,
                    start_time=form.cleaned_data['start_time'],
                    end_time=form.cleaned_data['end_time']
                )
                service.generate()
                
                if service.errors:
                    for err in service.errors:
                        messages.warning(request, err)
                if service.scheduled_count > 0:
                    messages.success(request, f"Successfully auto-generated {service.scheduled_count} schedules.")
                if service.skipped_count > 0:
                    messages.info(request, f"Skipped {service.skipped_count} locked schedules.")
            else:
                messages.error(request, "Invalid time format provided.")

        elif action == 'toggle_lock':
            sched_id = request.POST.get('schedule_id')
            sched = get_object_or_404(ExamSchedule, id=sched_id, exam=exam)
            sched.is_locked = not sched.is_locked
            sched.save()
            messages.success(request, f"Schedule for {sched.subject.code} {'locked' if sched.is_locked else 'unlocked'}.")

        elif action == 'delete':
            sched_id = request.POST.get('schedule_id')
            sched = get_object_or_404(ExamSchedule, id=sched_id, exam=exam)
            if not sched.is_locked:
                sched.delete()
                messages.success(request, f"Schedule for {sched.subject.code} removed.")
            else:
                messages.error(request, "Cannot delete a locked schedule.")

        elif action == 'edit':
            sched_id = request.POST.get('schedule_id')
            sched = get_object_or_404(ExamSchedule, id=sched_id, exam=exam)
            if not sched.is_locked:
                form = ExamScheduleEditForm(request.POST, instance=sched)
                if form.is_valid():
                    form.save()
                    messages.success(request, f"Schedule for {sched.subject.code} updated.")
                else:
                    messages.error(request, "Invalid input for schedule edit.")
            else:
                messages.error(request, "Cannot edit a locked schedule.")

        # Stay on the same tab
        active_tab = request.POST.get('tab', 'date')
        return redirect(f"{request.path}?tab={active_tab}")
