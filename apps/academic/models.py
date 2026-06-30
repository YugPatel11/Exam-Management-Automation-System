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
    start_date = models.DateField(
        null=True, blank=True,
        verbose_name="Start Date",
        help_text="Start date of the academic year."
    )
    end_date = models.DateField(
        null=True, blank=True,
        verbose_name="End Date",
        help_text="End date of the academic year."
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

    def check_and_trigger_exam_creation(self):
        """
        Check if all three required imports are complete for this Academic Year.
        If so, trigger automatic exam creation.
        The three required imports are:
        1. Academic Structure (semesters exist)
        2. Faculty Master (faculty_members exist)
        3. Teaching Allocation (teaching_assignments exist)
        """
        if (self.semesters.exists() and 
            self.faculty_members.exists() and 
            self.teaching_assignments.exists()):
            from apps.exams.services import ExamAutoGenerationService
            ExamAutoGenerationService.generate_exams_for_academic_year(self)


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


# ═══════════════════════════════════════════════════════
# FACULTY MASTER & TEACHING ALLOCATION
# ═══════════════════════════════════════════════════════

class FacultyMaster(BaseModel):
    """
    Faculty identity record, scoped to an Academic Year.
    Email ID is the primary identity key for authentication,
    notifications, and cross-module references.

    The same faculty may appear across multiple Academic Years —
    each year gets its own record so that name/department changes
    are tracked year-over-year.
    """
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='faculty_members',
        verbose_name="Academic Year"
    )
    faculty_name = models.CharField(
        max_length=255,
        verbose_name="Faculty Name",
        help_text="Full name as it appears in official records."
    )
    short_form = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Short Form / Alias",
        help_text="e.g., BBB, SJS, PSM — used for matching in allocation files."
    )
    email = models.EmailField(
        verbose_name="Official Email ID",
        help_text="Primary identity for login, notifications, and audit."
    )
    employee_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Employee Code",
        help_text="HR employee ID, if available."
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Department"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active",
        help_text="Whether this faculty is currently active for this academic year."
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='faculty_master_records',
        verbose_name="Linked User Account",
        help_text="Auto-linked if a User with the same email exists."
    )

    class Meta:
        unique_together = ('academic_year', 'email')
        ordering = ['faculty_name']
        verbose_name = "Faculty Master"
        verbose_name_plural = "Faculty Master Records"

    def __str__(self):
        alias = f" ({self.short_form})" if self.short_form else ""
        return f"{self.faculty_name}{alias}"


class FacultyTeachingAssignment(BaseModel):
    """
    Maps a faculty member to a subject and class within an Academic Year.

    Teaching type distinguishes:
        - 'Theory' → faculty teaches ALL students of the class
        - 'Practical-Batch-A', 'Practical-Batch-B', etc. → batch-specific

    The is_coordinator flag marks the Course Coordinator for this
    subject-class combination.
    """
    class TeachingType(models.TextChoices):
        COORDINATOR = 'coordinator', 'Course Coordinator'
        THEORY = 'theory', 'Theory (All Students)'
        PRACTICAL_BATCH_A = 'practical_batch_a', 'Practical / Tutorial — Batch A'
        PRACTICAL_BATCH_B = 'practical_batch_b', 'Practical / Tutorial — Batch B'
        PRACTICAL_BATCH_C = 'practical_batch_c', 'Practical / Tutorial — Batch C'

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='teaching_assignments',
        verbose_name="Academic Year"
    )
    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name='teaching_assignments',
        verbose_name="Semester"
    )
    semester_subject = models.ForeignKey(
        SemesterSubject,
        on_delete=models.PROTECT,
        related_name='teaching_assignments',
        verbose_name="Subject"
    )
    faculty = models.ForeignKey(
        FacultyMaster,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teaching_assignments',
        verbose_name="Faculty",
        help_text="Null for External / unresolved faculty."
    )
    class_name = models.CharField(
        max_length=100,
        verbose_name="Class",
        help_text="e.g., CV3, ME3, CE3+CSE3D, MLAI5B"
    )
    is_coordinator = models.BooleanField(
        default=False,
        verbose_name="Course Coordinator",
        help_text="Whether this faculty is the Course Coordinator for this subject."
    )
    teaching_type = models.CharField(
        max_length=30,
        choices=TeachingType.choices,
        default=TeachingType.THEORY,
        verbose_name="Teaching Type"
    )
    faculty_alias_raw = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Original Alias",
        help_text="The raw alias from the import file, kept for audit/debugging."
    )

    class Meta:
        ordering = ['semester', 'class_name', 'semester_subject']
        verbose_name = "Faculty Teaching Assignment"
        verbose_name_plural = "Faculty Teaching Assignments"

    def __str__(self):
        fac = self.faculty.short_form if self.faculty else self.faculty_alias_raw
        return (
            f"{self.class_name} → {self.semester_subject.subject_code} "
            f"({self.get_teaching_type_display()}) — {fac}"
        )


class FacultyImportLog(BaseModel):
    """
    Audit trail for Faculty Master and Teaching Allocation imports.
    """
    class ImportType(models.TextChoices):
        FACULTY_MASTER = 'faculty_master', 'Faculty Master'
        TEACHING_ALLOCATION = 'teaching_allocation', 'Teaching Allocation'

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
        related_name='faculty_imports',
        verbose_name="Academic Year"
    )
    import_type = models.CharField(
        max_length=25,
        choices=ImportType.choices,
        verbose_name="Import Type"
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
        related_name='faculty_imports',
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
        help_text="Statistics: records_created, records_updated, etc."
    )
    error_log = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Error Log",
        help_text="List of row-level errors encountered during import."
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Faculty Import Log"
        verbose_name_plural = "Faculty Import Logs"

    def __str__(self):
        return (
            f"{self.get_import_type_display()} for {self.academic_year.name} "
            f"— {self.original_filename} ({self.status})"
        )
