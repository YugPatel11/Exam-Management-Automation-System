"""
Services for automatic Exam and Marks Entry Task generation.
"""
from django.db import transaction
from django.utils.text import slugify
from apps.academic.models import Semester, MarksComponent, FacultyTeachingAssignment
from apps.exams.models import Exam
from apps.marks.models import MarksEntryTask


class ExamAutoGenerationService:
    """
    Handles automatic generation of Exams and MarksEntryTasks 
    when an Academic Year has all required Excel imports completed.
    """
    
    @classmethod
    @transaction.atomic
    def generate_exams_for_academic_year(cls, academic_year):
        """
        Creates exams and marks entry tasks for the academic year.
        Exams are created per unique MarksComponent name (e.g., "Theory CE").
        """
        # Ensure we have start and end dates (fallback to today if missing, though they should be required)
        from django.utils import timezone
        start_date = academic_year.start_date or timezone.now().date()
        end_date = academic_year.end_date or timezone.now().date()
        
        semesters = Semester.objects.filter(academic_year=academic_year)
        
        for semester in semesters:
            # Find all unique MarksComponent names in this semester
            component_names = MarksComponent.objects.filter(
                semester_subject__semester=semester,
                max_marks__gt=0
            ).values_list('name', flat=True).distinct()
            
            for comp_name in component_names:
                # Create the Exam for this component
                exam_name = f"Semester {semester.number} - {comp_name} ({academic_year.name})"
                
                exam, created = Exam.objects.get_or_create(
                    academic_year_ref=academic_year,
                    semester_ref=semester,
                    exam_type=comp_name,
                    defaults={
                        'name': exam_name,
                        'academic_year': academic_year.name,
                        'status': Exam.ExamStatus.SCHEDULED,
                        'start_date': start_date,
                        'end_date': end_date,
                        'marks_entry_start': start_date,
                        'marks_entry_end': end_date,
                    }
                )
                
                # If the exam already existed, we still want to make sure it has tasks,
                # so we continue to create MarksEntryTasks.
                
                # Find all teaching assignments in this semester where the subject has this component
                assignments = FacultyTeachingAssignment.objects.filter(
                    semester=semester,
                    faculty__isnull=False,  # only assign if there's a faculty member
                    semester_subject__marks_components__name=comp_name,
                    semester_subject__marks_components__max_marks__gt=0
                ).select_related('faculty__user', 'semester_subject__subject')
                
                for assignment in assignments:
                    # Skip if the faculty has no linked user account (they can't login to enter marks)
                    if not assignment.faculty.user:
                        continue
                        
                    MarksEntryTask.objects.get_or_create(
                        exam=exam,
                        subject=assignment.semester_subject.subject,
                        division=None,
                        teaching_assignment=assignment,
                        faculty=assignment.faculty.user,
                        defaults={
                            'semester_subject': assignment.semester_subject,
                            'status': 'pending'
                        }
                    )
