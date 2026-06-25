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
            plan.status = 'locked' if plan.is_locked else 'generated'
            plan.save()
            messages.success(request, f"Seating plan {'locked' if plan.is_locked else 'unlocked'}.")

        elif action == 'delete_allocation':
            plan = get_object_or_404(SeatingPlan, exam=exam)
            if plan.is_locked:
                messages.error(request, "Cannot edit a locked seating plan.")
            else:
                alloc_id = request.POST.get('allocation_id')
                alloc = get_object_or_404(SeatingAllocation, id=alloc_id, plan=plan)
                alloc.delete()
                messages.success(request, "Seat allocation removed.")

        elif action == 'swap':
            plan = get_object_or_404(SeatingPlan, exam=exam)
            if plan.is_locked:
                messages.error(request, "Cannot edit a locked seating plan.")
            else:
                alloc_id_1 = request.POST.get('allocation_id_1')
                alloc_id_2 = request.POST.get('allocation_id_2')
                alloc1 = get_object_or_404(SeatingAllocation, id=alloc_id_1, plan=plan)
                alloc2 = get_object_or_404(SeatingAllocation, id=alloc_id_2, plan=plan)
                # Swap seat assignments
                alloc1.classroom, alloc2.classroom = alloc2.classroom, alloc1.classroom
                alloc1.seat_number, alloc2.seat_number = alloc2.seat_number, alloc1.seat_number
                alloc1.save()
                alloc2.save()
                messages.success(request, f"Swapped seats for {alloc1.student.roll_no} and {alloc2.student.roll_no}.")

        elif action == 'edit_allocation':
            plan = get_object_or_404(SeatingPlan, exam=exam)
            if plan.is_locked:
                messages.error(request, "Cannot edit a locked seating plan.")
            else:
                alloc_id = request.POST.get('allocation_id')
                alloc = get_object_or_404(SeatingAllocation, id=alloc_id, plan=plan)
                new_classroom_id = request.POST.get('classroom_id')
                new_seat = request.POST.get('seat_number')
                if new_classroom_id:
                    alloc.classroom_id = new_classroom_id
                if new_seat:
                    alloc.seat_number = int(new_seat)
                alloc.save()
                messages.success(request, f"Allocation updated for {alloc.student.roll_no}.")
            
        active_tab = request.POST.get('tab', 'date')
        return redirect(f"{request.path}?tab={active_tab}")
