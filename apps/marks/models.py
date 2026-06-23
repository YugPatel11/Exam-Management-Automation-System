"""
Models for Marks Management.
"""
from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from apps.exams.models import Exam
from apps.master_data.models import Subject, Division
from apps.students.models import Student


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
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ('exam', 'subject', 'division', 'faculty')
        verbose_name = "Marks Entry Task"
        verbose_name_plural = "Marks Entry Tasks"

    def __str__(self):
        div_code = self.division.name if self.division else "All"
        return f"{self.subject.code} - {div_code} ({self.faculty.get_display_name()})"


class StudentMark(BaseModel):
    """
    Represents the marks obtained by a student for a specific task.
    Component marks are stored dynamically in a JSONField based on the Assessment Scheme.
    """
    task = models.ForeignKey(MarksEntryTask, on_delete=models.CASCADE, related_name='student_marks')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='marks')
    
    # Store dynamic marks like {"internal_1": 25, "internal_2": 30, "practical": 40}
    component_marks = models.JSONField(default=dict, blank=True)
    
    # Computed totals
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    is_absent = models.BooleanField(default=False)

    class Meta:
        unique_together = ('task', 'student')
        ordering = ['student__roll_no']
        verbose_name = "Student Mark"
        verbose_name_plural = "Student Marks"

    def __str__(self):
        return f"{self.student.roll_no} - {self.total_marks}"
