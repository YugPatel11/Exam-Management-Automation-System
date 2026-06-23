"""
Views for Seating Arrangement.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, View
from collections import defaultdict

from apps.core.mixins import ExamCoordinatorRequiredMixin
from apps.exams.models import Exam
from apps.seating.models import SeatingPlan, SeatingAllocation
from apps.seating.services import seating_generator_service
from apps.master_data.models import Classroom


class SeatingDashboardView(ExamCoordinatorRequiredMixin, ListView):
    """
    List of Exams for Exam Coordinators to manage their seating arrangements.
    """
    model = Exam
    template_name = 'seating/dashboard.html'
    context_object_name = 'exams'

    def get_queryset(self):
        return Exam.objects.all().prefetch_related('seating_plan')


class SeatingManagerView(ExamCoordinatorRequiredMixin, View):
    """
    Manages the seating plan for a specific Exam.
    Provides tabs for Date-wise, Room-wise, and Program-wise views.
    Handles Auto-Generate and Lock actions.
    """
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        plan, created = SeatingPlan.objects.get_or_create(exam=exam)
        
        allocations = SeatingAllocation.objects.filter(plan=plan).select_related(
            'schedule__subject', 'classroom', 'student__program'
        )
        
        active_tab = request.GET.get('tab', 'date')
        
        # Groupings
        date_wise = defaultdict(lambda: defaultdict(list))
        room_wise = defaultdict(lambda: defaultdict(list))
        program_wise = defaultdict(lambda: defaultdict(list))
        
        for a in allocations:
            date_key = (a.schedule.date, a.schedule.start_time, a.schedule.end_time)
            
            # Date -> Room -> Allocations
            date_wise[date_key][a.classroom].append(a)
            
            # Room -> Date -> Allocations
            room_wise[a.classroom][date_key].append(a)
            
            # Program -> Date -> Allocations
            program_wise[a.student.program][date_key].append(a)

        context = {
            'exam': exam,
            'plan': plan,
            'active_tab': active_tab,
            'date_wise': dict(date_wise),
            'room_wise': dict(room_wise),
            'program_wise': dict(program_wise),
            'total_allocated': allocations.count(),
        }
        return render(request, 'seating/manager.html', context)

    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        action = request.POST.get('action')
        
        if action == 'auto_generate':
            service = seating_generator_service(exam=exam)
            success = service.generate()
            
            if service.errors:
                for err in service.errors:
                    messages.error(request, err)
            elif success:
                messages.success(request, "Seating arrangement generated successfully.")
                
        elif action == 'toggle_lock':
            plan = get_object_or_404(SeatingPlan, exam=exam)
            plan.is_locked = not plan.is_locked
            plan.save()
            messages.success(request, f"Seating plan {'locked' if plan.is_locked else 'unlocked'}.")
            
        active_tab = request.POST.get('tab', 'date')
        return redirect(f"{request.path}?tab={active_tab}")
