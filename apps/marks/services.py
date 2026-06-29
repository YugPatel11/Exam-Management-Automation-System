"""
Services for Marks Management.
"""
import csv
import io
from django.db import transaction
from collections import defaultdict

from apps.marks.models import MarksEntryTask, StudentMark
from apps.faculty.models import SubjectFacultyAssignment
from apps.students.models import Student
from apps.master_data.models import Division


class MarksAllocationService:
    def __init__(self, exam):
        self.exam = exam
        self.errors = []
        self.allocated_count = 0

    def allocate(self):
        """
        Auto-allocates marks entry tasks to faculty based on FacultyTeachingAssignments.
        """
        if not self.exam.academic_year_ref or not self.exam.semester_ref:
            self.errors.append("Exam must have an Academic Year and Semester selected to auto-allocate marks.")
            return False

        from apps.academic.models import FacultyTeachingAssignment
        
        with transaction.atomic():
            # Get teaching assignments for the exam's semester
            assignments = FacultyTeachingAssignment.objects.filter(
                academic_year=self.exam.academic_year_ref,
                semester=self.exam.semester_ref
            ).select_related('faculty', 'semester_subject__subject')
            
            if not assignments.exists():
                self.errors.append("No faculty teaching assignments found for this exam's semester.")
                return False
                
            tasks_to_create = []
            # Existing tasks keyed by (exam_id, teaching_assignment_id)
            existing_tasks = set(MarksEntryTask.objects.filter(exam=self.exam).values_list('teaching_assignment_id', flat=True))
            
            for a in assignments:
                if not a.faculty or not a.faculty.user:
                    continue # Skip if faculty has no linked user account
                    
                if a.id not in existing_tasks:
                    tasks_to_create.append(
                        MarksEntryTask(
                            exam=self.exam,
                            subject=a.semester_subject.subject,
                            semester_subject=a.semester_subject,
                            teaching_assignment=a,
                            faculty=a.faculty.user,
                            status='pending'
                        )
                    )
                    existing_tasks.add(a.id)
                    self.allocated_count += 1
                    
            if tasks_to_create:
                MarksEntryTask.objects.bulk_create(tasks_to_create)
                
            return True


class MarksCsvImportService:
    def __init__(self, task, components):
        self.task = task
        self.components = components # List of dicts: [{'key': 'internal_1', 'max_marks': 25}, ...]
        self.errors = []
        self.success_count = 0
        
    def process(self, csv_file):
        """
        Processes an uploaded CSV file containing marks.
        Expected columns: RollNo, Absent, Component1_Key, Component2_Key, ...
        """
        try:
            # Read CSV
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            # Validate headers
            headers = reader.fieldnames
            if 'RollNo' not in headers:
                self.errors.append("CSV must contain a 'RollNo' column.")
                return False
                
            if 'Status' not in headers:
                self.errors.append("CSV must contain a 'Status' column (Present, AB, or UFM).")
                return False
                
            for comp in self.components:
                if comp['key'] not in headers:
                    self.errors.append(f"CSV must contain column for component: {comp['key']}")
                    return False
                    
            # Parse rows
            with transaction.atomic():
                # Delete existing unlocked marks
                if self.task.status != 'locked':
                    StudentMark.objects.filter(task=self.task).delete()
                else:
                    self.errors.append("Task is locked. Cannot import marks.")
                    return False
                    
                marks_to_create = []
                
                for row_num, row in enumerate(reader, start=2):
                    roll_no = row.get('RollNo', '').strip()
                    
                    try:
                        student = Student.objects.get(roll_no=roll_no)
                    except Student.DoesNotExist:
                        self.errors.append(f"Row {row_num}: Student with RollNo {roll_no} not found.")
                        continue
                        
                    status = str(row.get('Status', 'Present')).strip()
                    if status not in ['Present', 'AB', 'UFM']:
                        self.errors.append(f"Row {row_num}: Invalid status '{status}'. Must be Present, AB, or UFM.")
                        row_has_error = True
                        continue
                    
                    marks_dict = {}
                    total = 0
                    
                    if status in ['AB', 'UFM']:
                        for comp in self.components:
                            marks_dict[comp['key']] = 0
                    else:
                        for comp in self.components:
                            val_str = row.get(comp['key'], '0').strip()
                            try:
                                val = int(val_str)
                                if val < 0:
                                    self.errors.append(f"Row {row_num}: Marks cannot be negative.")
                                    row_has_error = True
                                    break
                                # If max_marks is known, validate it
                                if 'max_marks' in comp and comp['max_marks']:
                                    if val > comp['max_marks']:
                                        self.errors.append(f"Row {row_num}: Marks {val} for {comp['key']} out of range (max {comp['max_marks']}).")
                                        row_has_error = True
                                        break
                                marks_dict[comp['key']] = val
                                total += val
                            except ValueError:
                                self.errors.append(f"Row {row_num}: Invalid integer format for {comp['key']}.")
                                row_has_error = True
                                break
                                
                    if not row_has_error:
                        marks_to_create.append(
                            StudentMark(
                                task=self.task,
                                student=student,
                                component_marks=marks_dict,
                                total_marks=total,
                                status=status
                            )
                        )
                        self.success_count += 1
                        
                if marks_to_create:
                    StudentMark.objects.bulk_create(marks_to_create)
                    self.task.status = 'in_progress'
                    self.task.save()
                    
            return len(self.errors) == 0
            
        except Exception as e:
            self.errors.append(f"Error processing CSV: {str(e)}")
            return False
            
marks_allocation_service = MarksAllocationService
