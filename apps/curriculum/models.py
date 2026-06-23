"""
Models for Curriculum and Examination Scheme Management.
"""
from django.db import models
from apps.core.models import BaseModel
from apps.master_data.models import Program, Subject


class AssessmentScheme(BaseModel):
    """
    Defines the maximum marks structure for a Subject.
    A Subject has exactly one assessment scheme regardless of the program it is taught in.
    """
    subject = models.OneToOneField(
        Subject,
        on_delete=models.CASCADE,
        related_name='assessment_scheme',
        verbose_name="Subject"
    )
    
    # Theory Marks
    theory_ce = models.PositiveIntegerField(default=0, verbose_name="Theory CE Max Marks")
    theory_ese = models.PositiveIntegerField(default=0, verbose_name="Theory ESE Max Marks")
    
    # Practical Marks
    practical_ce = models.PositiveIntegerField(default=0, verbose_name="Practical CE Max Marks")
    practical_ese = models.PositiveIntegerField(default=0, verbose_name="Practical ESE Max Marks")
    
    # Tutorial Marks
    tutorial_ce = models.PositiveIntegerField(default=0, verbose_name="Tutorial CE Max Marks")
    tutorial_ese = models.PositiveIntegerField(default=0, verbose_name="Tutorial ESE Max Marks")

    class Meta:
        verbose_name = "Assessment Scheme"
        verbose_name_plural = "Assessment Schemes"

    def __str__(self):
        return f"Scheme for {self.subject.code}"


class CurriculumMapping(BaseModel):
    """
    Maps a Subject to a specific Program and Semester.
    """
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='curriculum_mappings'
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name='curriculum_mappings'
    )
    semester = models.PositiveIntegerField(verbose_name="Semester")

    class Meta:
        unique_together = ('subject', 'program', 'semester')
        ordering = ['program', 'semester', 'subject']
        verbose_name = "Curriculum Mapping"
        verbose_name_plural = "Curriculum Mappings"

    def __str__(self):
        return f"{self.subject.code} in {self.program.code} (Sem {self.semester})"
