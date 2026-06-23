"""
Models for Exam Scheduling.
"""
from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import BaseModel
from apps.exams.models import Exam
from apps.master_data.models import Subject


class ExamSchedule(BaseModel):
    """
    Represents the scheduled date and time for a specific subject within an exam event.
    """
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='exam_schedules'
    )
    date = models.DateField(
        verbose_name="Exam Date"
    )
    start_time = models.TimeField(
        verbose_name="Start Time"
    )
    end_time = models.TimeField(
        verbose_name="End Time"
    )
    is_locked = models.BooleanField(
        default=False,
        verbose_name="Is Locked",
        help_text="If locked, auto-generation will not overwrite this record."
    )

    class Meta:
        unique_together = ('exam', 'subject')
        ordering = ['date', 'start_time', 'subject__code']
        verbose_name = "Exam Schedule"
        verbose_name_plural = "Exam Schedules"

    def __str__(self):
        return f"{self.subject.code} - {self.date} ({self.start_time.strftime('%H:%M')} to {self.end_time.strftime('%H:%M')})"

    def clean(self):
        super().clean()
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("End time must be after start time.")
        
        if self.exam and self.date:
            if self.date < self.exam.start_date or self.date > self.exam.end_date:
                raise ValidationError(f"Date must be within the exam window: {self.exam.start_date} to {self.exam.end_date}.")
