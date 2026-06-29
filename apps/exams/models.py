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

    Now linked to AcademicYear and Semester via ForeignKeys for the
    new academic-year-first workflow.
    """
    class ExamType(models.TextChoices):
        THEORY_CE = 'THEORY_CE', 'Theory CE'
        THEORY_ESE = 'THEORY_ESE', 'Theory ESE'
        PRACTICAL_CE = 'PRACTICAL_CE', 'Practical CE'
        PRACTICAL_ESE = 'PRACTICAL_ESE', 'Practical ESE'
        TUTORIAL_CE = 'TUTORIAL_CE', 'Tutorial CE'
        TUTORIAL_ESE = 'TUTORIAL_ESE', 'Tutorial ESE'
        I1 = 'I1', 'I1 Examination'
        I2 = 'I2', 'I2 Examination'
        IMPROVEMENT = 'Improvement', 'Improvement Examination'
        FE = 'FE', 'FE Examination'

    class ExamStatus(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SCHEDULED = 'scheduled', 'Scheduled'
        ONGOING = 'ongoing', 'Ongoing'
        COMPLETED = 'completed', 'Completed'

    # ──── New: FK-based Academic Year & Semester ────
    academic_year_ref = models.ForeignKey(
        'academic.AcademicYear',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='exams',
        verbose_name="Academic Year",
        help_text="Select the Academic Year this exam belongs to."
    )
    semester_ref = models.ForeignKey(
        'academic.Semester',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='exams',
        verbose_name="Semester",
        help_text="Select the semester for this exam."
    )

    # ──── Legacy: kept for backward compatibility ────
    academic_year = models.CharField(
        max_length=7,
        validators=[
            RegexValidator(
                regex=r'^\d{4}-\d{2}$',
                message="Format must be YYYY-YY (e.g., 2023-24)"
            )
        ],
        help_text="Format: YYYY-YY (e.g., 2023-24)",
        verbose_name="Academic Year (Legacy)",
        blank=True,
        default='',
    )
    
    name = models.CharField(
        max_length=255, 
        verbose_name="Exam Name",
        help_text="e.g., Mid Semester 1 Examination"
    )
    
    exam_type = models.CharField(
        max_length=20,
        choices=ExamType.choices,
        default=ExamType.THEORY_CE,
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
        help_text="Select the programs participating in this exam.",
        blank=True,
    )
    
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(verbose_name="End Date")

    # Marks entry window — faculty can only enter marks during this period
    marks_entry_start = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Marks Entry Start",
        help_text="Faculty can begin entering marks from this date/time."
    )
    marks_entry_end = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Marks Entry End",
        help_text="Faculty must finish entering marks by this date/time."
    )

    class Meta:
        ordering = ['-start_date']
        verbose_name = "Exam"
        verbose_name_plural = "Exams"

    def __str__(self):
        ay = self.academic_year_ref.name if self.academic_year_ref else self.academic_year
        return f"{self.name} ({ay})"

    def save(self, *args, **kwargs):
        # Sync legacy field from FK
        if self.academic_year_ref and not self.academic_year:
            self.academic_year = self.academic_year_ref.name
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError({
                    'end_date': 'End date cannot be earlier than start date.'
                })
        # Validate semester belongs to the selected academic year
        if self.academic_year_ref and self.semester_ref:
            if self.semester_ref.academic_year != self.academic_year_ref:
                raise ValidationError({
                    'semester_ref': 'Selected semester does not belong to the selected academic year.'
                })
