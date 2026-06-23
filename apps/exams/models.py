"""
Models for Exam Management.
"""
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.models import BaseModel
from apps.master_data.models import Program


class Exam(BaseModel):
    """
    Core entity representing an examination event (e.g., Mid Semester 1).
    Acts as the parent container for schedules, seating, and marks.
    """
    class ExamType(models.TextChoices):
        INTERNAL_1 = 'internal_1', 'Internal 1'
        INTERNAL_2 = 'internal_2', 'Internal 2'
        CONTINUOUS = 'continuous', 'Continuous Evaluation'
        OTHER = 'other', 'Other'

    class ExamStatus(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SCHEDULED = 'scheduled', 'Scheduled'
        ONGOING = 'ongoing', 'Ongoing'
        COMPLETED = 'completed', 'Completed'

    academic_year = models.CharField(
        max_length=7,
        validators=[
            RegexValidator(
                regex=r'^\d{4}-\d{2}$',
                message="Format must be YYYY-YY (e.g., 2023-24)"
            )
        ],
        help_text="Format: YYYY-YY (e.g., 2023-24)",
        verbose_name="Academic Year"
    )
    
    name = models.CharField(
        max_length=255, 
        verbose_name="Exam Name",
        help_text="e.g., Mid Semester 1 Examination"
    )
    
    exam_type = models.CharField(
        max_length=20,
        choices=ExamType.choices,
        default=ExamType.INTERNAL_1,
        verbose_name="Exam Type"
    )
    
    status = models.CharField(
        max_length=20,
        choices=ExamStatus.choices,
        default=ExamStatus.DRAFT,
        verbose_name="Exam Status"
    )

    programs = models.ManyToManyField(
        Program,
        related_name='exams',
        verbose_name="Applicable Programs",
        help_text="Select the programs participating in this exam."
    )
    
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(verbose_name="End Date")

    class Meta:
        ordering = ['-academic_year', '-start_date']
        verbose_name = "Exam"
        verbose_name_plural = "Exams"

    def __str__(self):
        return f"{self.name} ({self.academic_year})"

    def clean(self):
        super().clean()
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError({
                    'end_date': 'End date cannot be earlier than start date.'
                })
