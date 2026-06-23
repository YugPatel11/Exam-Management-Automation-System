"""
Models for Duty Chart Management.
"""
from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from apps.exams.models import Exam
from apps.master_data.models import Classroom


class DutyChart(BaseModel):
    """
    Represents the full supervision duty chart for an exam.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('locked', 'Locked'),
    ]

    exam = models.OneToOneField(Exam, on_delete=models.CASCADE, related_name='duty_chart')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_locked = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Duty Chart"
        verbose_name_plural = "Duty Charts"

    def __str__(self):
        return f"Duty Chart for {self.exam.name}"


class DutyAssignment(BaseModel):
    """
    Represents a supervision duty assigned to a faculty member for a specific session and room.
    """
    chart = models.ForeignKey(DutyChart, on_delete=models.CASCADE, related_name='assignments')
    
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='duty_assignments')
    faculty = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='duty_assignments')

    class Meta:
        # A faculty can only be assigned to one room per session
        unique_together = ('date', 'start_time', 'end_time', 'faculty')
        ordering = ['date', 'start_time', 'classroom__room_number']
        verbose_name = "Duty Assignment"
        verbose_name_plural = "Duty Assignments"

    def __str__(self):
        return f"{self.faculty.get_display_name()} - {self.classroom.room_number} on {self.date}"
