"""
Services for Duty Chart Management.
"""
from django.db import transaction
from collections import defaultdict
from itertools import cycle

from apps.duty_chart.models import DutyChart, DutyAssignment
from apps.scheduling.models import ExamSchedule
from apps.seating.models import SeatingPlan, SeatingAllocation
from apps.accounts.models import User


class DutyChartGeneratorService:
    def __init__(self, exam):
        self.exam = exam
        self.errors = []

    def generate(self):
        """
        Generates the duty chart for the exam.
        Strategy:
        Find all distinct sessions (date, start_time, end_time) that have seating allocations.
        For each session, find which classrooms are in use.
        Assign a faculty member to each classroom in use.
        Use round-robin distribution to balance the workload across all available faculty.
        """
        with transaction.atomic():
            chart, created = DutyChart.objects.get_or_create(exam=self.exam)
            
            if chart.is_locked:
                self.errors.append("Duty chart is locked. Unlock it to regenerate.")
                return False
                
            # Clear existing unlocked assignments
            DutyAssignment.objects.filter(chart=chart).delete()
            
            try:
                seating_plan = self.exam.seating_plan
                if not seating_plan or seating_plan.status == 'draft':
                    self.errors.append("Seating arrangement must be generated before duty chart.")
                    return False
            except SeatingPlan.DoesNotExist:
                self.errors.append("Seating arrangement must be generated before duty chart.")
                return False
                
            allocations = SeatingAllocation.objects.filter(plan=seating_plan).select_related('schedule', 'classroom')
            
            if not allocations.exists():
                self.errors.append("No seating allocations found.")
                return False
                
            # Find distinct classrooms per session
            session_classrooms = defaultdict(set)
            for a in allocations:
                session_key = (a.schedule.date, a.schedule.start_time, a.schedule.end_time)
                session_classrooms[session_key].add(a.classroom)
                
            # Get all available faculty
            faculty_list = list(User.objects.filter(role__in=['subject_faculty', 'subject_coordinator', 'exam_coordinator']).order_by('id'))
            if not faculty_list:
                self.errors.append("No faculty available for duties.")
                return False
                
            faculty_cycle = cycle(faculty_list)
            
            assignments_to_create = []
            
            for session_key, classrooms in session_classrooms.items():
                date, start_time, end_time = session_key
                
                # Keep track of who is already assigned in this session
                assigned_this_session = set()
                
                for classroom in classrooms:
                    # Find next available faculty who hasn't been assigned to this session yet
                    faculty = next(faculty_cycle)
                    attempts = 0
                    while faculty.id in assigned_this_session:
                        faculty = next(faculty_cycle)
                        attempts += 1
                        if attempts > len(faculty_list):
                            self.errors.append(f"Not enough faculty for session on {date}. Need {len(classrooms)}, have {len(faculty_list)}")
                            return False
                            
                    assigned_this_session.add(faculty.id)
                    
                    assignments_to_create.append(
                        DutyAssignment(
                            chart=chart,
                            date=date,
                            start_time=start_time,
                            end_time=end_time,
                            classroom=classroom,
                            faculty=faculty
                        )
                    )
                    
            if assignments_to_create:
                DutyAssignment.objects.bulk_create(assignments_to_create)
                
            chart.status = 'generated'
            chart.save()
            return True
            
duty_chart_generator_service = DutyChartGeneratorService
