"""
Models for Assessment Scheme Configuration.
"""
from django.db import models
from django.core.validators import RegexValidator
from apps.core.models import BaseModel
from apps.master_data.models import Subject


class AssessmentComponent(BaseModel):
    """
    A granular component of an assessment (e.g., Internal 1, FE) designed by the Subject Coordinator.
    """
    PARENT_TYPE_CHOICES = [
        ('theory_ce', 'Theory CE'),
        ('theory_ese', 'Theory ESE'),
        ('practical_ce', 'Practical CE'),
        ('practical_ese', 'Practical ESE'),
        ('tutorial_ce', 'Tutorial CE'),
        ('tutorial_ese', 'Tutorial ESE'),
    ]

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='assessment_components'
    )
    parent_type = models.CharField(
        max_length=20,
        choices=PARENT_TYPE_CHOICES,
        verbose_name="Parent Component Type"
    )
    name = models.CharField(max_length=100, verbose_name="Component Name", help_text="e.g., Internal 1")
    variable_name = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^[a-zA-Z_][a-zA-Z0-9_]*$', 'Only alphanumeric and underscores allowed. Must start with a letter.')],
        verbose_name="Variable Name",
        help_text="Short name used in formulas (e.g., I1)"
    )
    max_marks = models.PositiveIntegerField(
        verbose_name="Maximum Marks",
        help_text="The conducted maximum marks for this component."
    )

    class Meta:
        unique_together = (
            ('subject', 'parent_type', 'name'),
            ('subject', 'parent_type', 'variable_name')
        )
        ordering = ['subject', 'parent_type', 'name']
        verbose_name = "Assessment Component"
        verbose_name_plural = "Assessment Components"

    def __str__(self):
        return f"{self.subject.code} - {self.get_parent_type_display()} - {self.name} ({self.variable_name})"


