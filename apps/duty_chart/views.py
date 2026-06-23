"""
Views for Duty Chart Arrangement.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, View
from collections import defaultdict

from apps.core.mixins import ExamCoordinatorRequiredMixin
from apps.exams.models import Exam
from apps.duty_chart.models import DutyChart, DutyAssignment
from apps.duty_chart.services import duty_chart_generator_service
from apps.accounts.models import User


class DutyChartDashboardView(ExamCoordinatorRequiredMixin, ListView):
    """
    List of Exams for Exam Coordinators to manage their duty charts.
    """
    model = Exam
    template_name = 'duty_chart/dashboard.html'
    context_object_name = 'exams'

    def get_queryset(self):
        return Exam.objects.all().prefetch_related('duty_chart')


class DutyChartManagerView(ExamCoordinatorRequiredMixin, View):
    """
    Manages the duty chart for a specific Exam.
    Provides tabs for Date-wise, Room-wise, and Faculty-wise views.
    Handles Auto-Generate and Lock actions.
    """
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        chart, created = DutyChart.objects.get_or_create(exam=exam)
        
        assignments = DutyAssignment.objects.filter(chart=chart).select_related(
            'classroom', 'faculty'
        )
        
        active_tab = request.GET.get('tab', 'date')
        
        # Groupings
        date_wise = defaultdict(list)
        room_wise = defaultdict(list)
        faculty_wise = defaultdict(list)
        
        for a in assignments:
            date_key = (a.date, a.start_time, a.end_time)
            
            # Date -> Assignments
            date_wise[date_key].append(a)
            
            # Room -> Assignments
            room_wise[a.classroom].append(a)
            
            # Faculty -> Assignments
            faculty_wise[a.faculty].append(a)

        context = {
            'exam': exam,
            'chart': chart,
            'active_tab': active_tab,
            'date_wise': dict(date_wise),
            'room_wise': dict(room_wise),
            'faculty_wise': dict(faculty_wise),
            'total_assigned': assignments.count(),
        }
        return render(request, 'duty_chart/manager.html', context)

    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        action = request.POST.get('action')
        
        if action == 'auto_generate':
            service = duty_chart_generator_service(exam=exam)
            success = service.generate()
            
            if service.errors:
                for err in service.errors:
                    messages.error(request, err)
            elif success:
                messages.success(request, "Duty chart generated successfully.")
                
        elif action == 'toggle_lock':
            chart = get_object_or_404(DutyChart, exam=exam)
            chart.is_locked = not chart.is_locked
            chart.save()
            messages.success(request, f"Duty chart {'locked' if chart.is_locked else 'unlocked'}.")
            
        active_tab = request.POST.get('tab', 'date')
        return redirect(f"{request.path}?tab={active_tab}")
