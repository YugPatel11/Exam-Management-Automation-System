"""
Models for Seating Arrangement.
"""
from django.db import models
from apps.core.models import BaseModel
from apps.exams.models import Exam
from apps.master_data.models import Classroom
from apps.scheduling.models import ExamSchedule
from apps.students.models import Student


class SeatingPlan(BaseModel):
    """
    Represents the complete seating plan for an exam event.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('locked', 'Locked'),
    ]

    exam = models.OneToOneField(Exam, on_delete=models.CASCADE, related_name='seating_plan')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_locked = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Seating Plan"
        verbose_name_plural = "Seating Plans"

    def __str__(self):
        return f"Seating Plan for {self.exam.name}"


class SeatingAllocation(BaseModel):
    """
    Represents a specific seat allocation for a student during a particular exam schedule.
    """
    plan = models.ForeignKey(SeatingPlan, on_delete=models.CASCADE, related_name='allocations')
    schedule = models.ForeignKey(ExamSchedule, on_delete=models.CASCADE, related_name='seating_allocations')
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='seating_allocations')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='seating_allocations')
    
    seat_number = models.PositiveIntegerField(help_text="Sequence number within the classroom")

    class Meta:
        unique_together = ('schedule', 'student')
        ordering = ['schedule__date', 'schedule__start_time', 'classroom__room_number', 'seat_number']
        verbose_name = "Seating Allocation"
        verbose_name_plural = "Seating Allocations"

    def __str__(self):
        return f"{self.student.roll_no} - {self.classroom.room_number} (Seat {self.seat_number})"
