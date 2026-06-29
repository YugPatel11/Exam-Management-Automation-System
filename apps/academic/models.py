"""
Models for Academic Year Management.

Hierarchy:
    AcademicYear → Semester → SemesterSubject → MarksComponent
    AcademicYear → AcademicStructureImport (audit trail)
"""
from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils.text import slugify
from apps.core.models import BaseModel
from apps.master_data.models import Subject


class AcademicYear(BaseModel):
    """
    Top-level entity representing an academic year (e.g., 2023-24).
    Everything — semesters, subjects, exams, marks — belongs to one AcademicYear.
    """
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        CLOSED = 'closed', 'Closed'
        ARCHIVED = 'archived', 'Archived'

    name = models.CharField(
        max_length=7,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{4}-\d{2}$',
                message="Format must be YYYY-YY (e.g., 2023-24)"
            )
        ],
        verbose_name="Academic Year",
        help_text="Format: YYYY-YY (e.g., 2023-24)"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="Optional description or notes for this academic year."
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Status"
    )

    class Meta:
        ordering = ['-name']
        verbose_name = "Academic Year"
        verbose_name_plural = "Academic Years"

    def __str__(self):
        return self.name

    @property
    def total_semesters(self):
        return self.semesters.count()

    @property
    def total_subjects(self):
        return SemesterSubject.objects.filter(semester__academic_year=self).count()

    @property
    def total_components(self):
        return MarksComponent.objects.filter(
            semester_subject__semester__academic_year=self
        ).count()

    @property
    def latest_import(self):
        return self.imports.order_by('-created_at').first()


class Semester(BaseModel):
    """
    A semester within an Academic Year.
    Auto-created during structure import.
    """
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='semesters',
        verbose_name="Academic Year"
    )
    number = models.PositiveIntegerField(
        verbose_name="Semester Number",
        help_text="e.g., 1, 2, 3, 4, 5, 6"
    )
    name = models.CharField(
        max_length=50,
        verbose_name="Semester Name",
        help_text="e.g., Semester 1"
    )

    class Meta:
        unique_together = ('academic_year', 'number')
        ordering = ['academic_year', 'number']
        verbose_name = "Semester"
        verbose_name_plural = "Semesters"

    def __str__(self):
        return f"{self.name} ({self.academic_year.name})"

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = f"Semester {self.number}"
        super().save(*args, **kwargs)

    @property
    def total_subjects(self):
        return self.semester_subjects.count()


class SemesterSubject(BaseModel):
    """
    Maps a Subject to a Semester within an Academic Year.
    Created automatically during structure import.
    """
    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name='semester_subjects',
        verbose_name="Semester"
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name='semester_subjects',
        verbose_name="Subject"
    )
    # Denormalized fields for display performance and import traceability
    subject_code = models.CharField(
        max_length=50,
        verbose_name="Subject Code",
        help_text="Snapshot of the subject code at import time."
    )
    subject_name = models.CharField(
        max_length=255,
        verbose_name="Subject Name",
        help_text="Snapshot of the subject name at import time."
    )

    class Meta:
        unique_together = ('semester', 'subject')
        ordering = ['semester', 'subject_code']
        verbose_name = "Semester Subject"
        verbose_name_plural = "Semester Subjects"

    def __str__(self):
        return f"{self.subject_code} - {self.subject_name} (Sem {self.semester.number})"

    @property
    def total_max_marks(self):
        """Sum of all marks components for this subject."""
        return self.marks_components.aggregate(
            total=models.Sum('max_marks')
        )['total'] or 0

    @property
    def active_components(self):
        """Returns only components with max_marks > 0."""
        return self.marks_components.filter(max_marks__gt=0)


class MarksComponent(BaseModel):
    """
    A single, dynamic marks component for a subject.

    Fully dynamic — component names come from the uploaded file headers.
    Examples: Theory CE, Theory ESE, Practical CE, Practical ESE,
              Tutorial CE, Tutorial ESE, Viva, Project, Assignment, Internal, External.

    No hardcoded list. Any component name is supported.
    """
    semester_subject = models.ForeignKey(
        SemesterSubject,
        on_delete=models.CASCADE,
        related_name='marks_components',
        verbose_name="Semester Subject"
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Component Name",
        help_text="e.g., Theory CE, Practical ESE, Viva, Project"
    )
    slug = models.SlugField(
        max_length=100,
        verbose_name="Component Slug",
        help_text="Auto-generated URL-safe identifier used as key in marks JSONField."
    )
    max_marks = models.PositiveIntegerField(
        verbose_name="Maximum Marks",
        help_text="Maximum obtainable marks for this component."
    )
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Display Order",
        help_text="Controls the order components appear in the UI."
    )

    class Meta:
        unique_together = ('semester_subject', 'slug')
        ordering = ['semester_subject', 'display_order', 'name']
        verbose_name = "Marks Component"
        verbose_name_plural = "Marks Components"

    def __str__(self):
        return f"{self.semester_subject.subject_code} → {self.name} ({self.max_marks})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name).replace('-', '_')
        super().save(*args, **kwargs)


class AcademicStructureImport(BaseModel):
    """
    Audit trail for academic structure imports.
    Records who imported what, when, and the results.
    """
    class ImportStatus(models.TextChoices):
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'
        PARTIAL = 'partial', 'Partial'

    class FileFormat(models.TextChoices):
        CSV = 'csv', 'CSV'
        XLSX = 'xlsx', 'Excel (XLSX)'

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='imports',
        verbose_name="Academic Year"
    )
    original_filename = models.CharField(
        max_length=255,
        verbose_name="Original Filename"
    )
    file_format = models.CharField(
        max_length=4,
        choices=FileFormat.choices,
        verbose_name="File Format"
    )
    imported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='academic_imports',
        verbose_name="Imported By"
    )
    status = models.CharField(
        max_length=10,
        choices=ImportStatus.choices,
        default=ImportStatus.SUCCESS,
        verbose_name="Import Status"
    )
    summary = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Import Summary",
        help_text="Statistics: semesters_created, subjects_created, components_created, etc."
    )
    error_log = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Error Log",
        help_text="List of row-level errors encountered during import."
    )
    program_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Detected Program",
        help_text="Program name auto-detected from file title."
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Academic Structure Import"
        verbose_name_plural = "Academic Structure Imports"

    def __str__(self):
        return f"Import for {self.academic_year.name} — {self.original_filename} ({self.status})"
