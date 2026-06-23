"""
Services for Seating Arrangement.
"""
from django.db import transaction
from collections import defaultdict
from itertools import cycle

from apps.seating.models import SeatingPlan, SeatingAllocation
from apps.scheduling.models import ExamSchedule
from apps.master_data.models import Classroom
from apps.curriculum.models import CurriculumMapping
from apps.students.models import Student


class SeatingGeneratorService:
    def __init__(self, exam):
        self.exam = exam
        self.errors = []
        
    def _get_students_for_subject(self, subject):
        """Get all students registered for a subject through curriculum mapping."""
        mappings = CurriculumMapping.objects.filter(subject=subject).select_related('program')
        students = []
        for mapping in mappings:
            qs = Student.objects.filter(
                program=mapping.program,
                semester=mapping.semester
            )
            students.extend(list(qs))
        return list(set(students)) # Ensure unique

    def generate(self):
        """
        Generates the seating arrangement.
        Strategy:
        Group schedules by Date + Session (Start/End time).
        For each session:
        - Gather all students writing an exam in this session.
        - Segregate students by subject/program.
        - Get all available classrooms ordered by capacity (descending).
        - Allocate seats sequentially across classrooms.
        - Mix students from different subjects to prevent copying (e.g. Sub1, Sub2, Sub1, Sub2).
        """
        with transaction.atomic():
            plan, created = SeatingPlan.objects.get_or_create(exam=self.exam)
            
            if plan.is_locked:
                self.errors.append("Seating plan is locked. Unlock it to regenerate.")
                return False
                
            # Clear existing unlocked allocations
            SeatingAllocation.objects.filter(plan=plan).delete()
            
            schedules = ExamSchedule.objects.filter(exam=self.exam).select_related('subject')
            if not schedules.exists():
                self.errors.append("No schedules found for this exam. Generate schedule first.")
                return False
                
            classrooms = list(Classroom.objects.all().order_by('-capacity'))
            if not classrooms:
                self.errors.append("No classrooms found in Master Data.")
                return False
                
            # Group schedules by session: (date, start_time, end_time)
            sessions = defaultdict(list)
            for s in schedules:
                sessions[(s.date, s.start_time, s.end_time)].append(s)
                
            allocations_to_create = []
            
            for session_key, session_schedules in sessions.items():
                date, start_time, end_time = session_key
                
                # Dictionary of schedule -> list of students
                schedule_students = {}
                total_students = 0
                
                for schedule in session_schedules:
                    students = self._get_students_for_subject(schedule.subject)
                    # Sort students by roll_no
                    students.sort(key=lambda s: s.roll_no)
                    schedule_students[schedule] = students
                    total_students += len(students)
                    
                total_capacity = sum(c.capacity for c in classrooms)
                if total_students > total_capacity:
                    self.errors.append(f"Not enough classroom capacity on {date}. Needed: {total_students}, Available: {total_capacity}")
                    return False
                
                # Interleave students from different schedules to mix subjects
                mixed_student_queue = []
                schedules_list = list(session_schedules)
                
                # A simple round-robin popping from each schedule's student list
                while any(schedule_students.values()):
                    for schedule in schedules_list:
                        if schedule_students[schedule]:
                            mixed_student_queue.append(
                                (schedule, schedule_students[schedule].pop(0))
                            )
                            
                # Now allocate to classrooms
                queue_index = 0
                for classroom in classrooms:
                    if queue_index >= len(mixed_student_queue):
                        break # All students allocated
                        
                    for seat_num in range(1, classroom.capacity + 1):
                        if queue_index >= len(mixed_student_queue):
                            break
                            
                        schedule, student = mixed_student_queue[queue_index]
                        
                        allocations_to_create.append(
                            SeatingAllocation(
                                plan=plan,
                                schedule=schedule,
                                classroom=classroom,
                                student=student,
                                seat_number=seat_num
                            )
                        )
                        queue_index += 1
                        
            if allocations_to_create:
                SeatingAllocation.objects.bulk_create(allocations_to_create)
                
            plan.status = 'generated'
            plan.save()
            return True
            
seating_generator_service = SeatingGeneratorService
