"""
Models for Marks Management.
"""
from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from apps.exams.models import Exam
from apps.master_data.models import Subject, Division


class MarksEntryTask(BaseModel):
    """
    Represents a task assigned to a faculty member to enter marks for a subject/division.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Entry'),
        ('in_progress', 'Draft / In Progress'),
        ('submitted', 'Submitted for Review'),
        ('locked', 'Locked / Finalized'),
    ]

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='marks_tasks')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='marks_tasks')
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='marks_tasks', null=True, blank=True)
    faculty = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='marks_tasks')

    # ──── New: Link to SemesterSubject for dynamic marks components ────
    semester_subject = models.ForeignKey(
        'academic.SemesterSubject',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marks_tasks',
        verbose_name="Semester Subject",
        help_text="Links this task to the academic structure for dynamic marks components."
    )
    
    teaching_assignment = models.ForeignKey(
        'academic.FacultyTeachingAssignment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marks_tasks',
        verbose_name="Teaching Assignment",
        help_text="Links this task to the specific class and batch assignment."
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ('exam', 'subject', 'division', 'teaching_assignment', 'faculty')
        verbose_name = "Marks Entry Task"
        verbose_name_plural = "Marks Entry Tasks"

    def __str__(self):
        if self.teaching_assignment:
            return f"{self.subject.code} - {self.teaching_assignment.class_name} ({self.faculty.get_display_name()})"
        div_code = self.division.name if self.division else "All"
        return f"{self.subject.code} - {div_code} ({self.faculty.get_display_name()})"

    def get_marks_components(self):
        """
        Returns the marks components for this task.
        Tries the new SemesterSubject first, falls back to legacy AssessmentScheme.
        """
        if self.semester_subject:
            from apps.academic.models import MarksComponent
            return [
                {
                    'key': mc.slug,
                    'label': mc.name,
                    'max_marks': mc.max_marks,
                }
                for mc in MarksComponent.objects.filter(
                    semester_subject=self.semester_subject,
                    max_marks__gt=0,
                ).order_by('display_order')
            ]
        else:
            # Legacy fallback: use AssessmentScheme
            try:
                scheme = self.subject.assessment_scheme
                components = []
                if scheme.theory_ce > 0:
                    components.append({'key': 'theory_ce', 'label': 'Theory CE', 'max_marks': scheme.theory_ce})
                if scheme.theory_ese > 0:
                    components.append({'key': 'theory_ese', 'label': 'Theory ESE', 'max_marks': scheme.theory_ese})
                if scheme.practical_ce > 0:
                    components.append({'key': 'practical_ce', 'label': 'Practical CE', 'max_marks': scheme.practical_ce})
                if scheme.practical_ese > 0:
                    components.append({'key': 'practical_ese', 'label': 'Practical ESE', 'max_marks': scheme.practical_ese})
                if scheme.tutorial_ce > 0:
                    components.append({'key': 'tutorial_ce', 'label': 'Tutorial CE', 'max_marks': scheme.tutorial_ce})
                if scheme.tutorial_ese > 0:
                    components.append({'key': 'tutorial_ese', 'label': 'Tutorial ESE', 'max_marks': scheme.tutorial_ese})
                return components
            except Exception:
                return []


class StudentMark(BaseModel):
    """
    Represents the marks obtained by a student for a specific task.
    Component marks are stored dynamically in a JSONField based on the Assessment Scheme.
    """
    task = models.ForeignKey(MarksEntryTask, on_delete=models.CASCADE, related_name='student_marks')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='marks')
    
    # Store dynamic marks like {"theory_ce": 25, "theory_ese": 30, "practical_ce": 40}
    component_marks = models.JSONField(default=dict, blank=True)
    
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('AB', 'Absent'),
        ('UFM', 'Unfair Means'),
    ]
    
    # Computed totals
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Present')

    class Meta:
        unique_together = ('task', 'student')
        ordering = ['student__roll_no']
        verbose_name = "Student Mark"
        verbose_name_plural = "Student Marks"

    def __str__(self):
        return f"{self.student.roll_no} - {self.total_marks}"
