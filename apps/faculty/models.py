"""
Models for Faculty Assignment Management.
"""
from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from apps.master_data.models import Subject


class SubjectCoordinatorAssignment(BaseModel):
    """
    Links a Subject to its Subject Coordinator.
    """
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='coordinator_assignments'
    )
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coordinated_subjects',
        help_text="The faculty member designated as the Subject Coordinator."
    )

    class Meta:
        unique_together = ('subject', 'coordinator')
        ordering = ['subject', 'coordinator']
        verbose_name = "Subject Coordinator Assignment"
        verbose_name_plural = "Subject Coordinator Assignments"

    def __str__(self):
        return f"{self.subject.code} - Coordinator: {self.coordinator.get_display_name()}"


class SubjectFacultyAssignment(BaseModel):
    """
    Links a Subject to a teaching Faculty member for a specific Division.
    """
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='faculty_assignments'
    )
    faculty = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='taught_subjects',
        help_text="The faculty member teaching this subject."
    )
    division_name = models.CharField(
        max_length=50,
        verbose_name="Division",
        help_text="Text label for the division (e.g., 'A', 'B')"
    )

    class Meta:
        unique_together = ('subject', 'faculty', 'division_name')
        ordering = ['subject', 'division_name', 'faculty']
        verbose_name = "Subject Faculty Assignment"
        verbose_name_plural = "Subject Faculty Assignments"

    def __str__(self):
        return f"{self.subject.code} (Div {self.division_name}) - Faculty: {self.faculty.get_display_name()}"
