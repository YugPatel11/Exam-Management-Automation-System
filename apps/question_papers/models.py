"""
Models for Question Paper Management.
"""
from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from apps.exams.models import Exam
from apps.master_data.models import Subject, Program


class QuestionPaperTemplate(BaseModel):
    """
    Template configured by the Exam Coordinator for Question Papers.
    Holds the rich HTML header and layout.
    """
    name = models.CharField(max_length=100, default="Standard Template")
    header_html = models.TextField(
        verbose_name="Header HTML Template",
        help_text="Use placeholders like {{ subject_code }}, {{ date }}, {{ questions }}, etc.",
        default="<div style='text-align:center;'><h1>College Name</h1><h2>{{ subject_code }} - {{ subject_name }}</h2></div>"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Question Paper Template"
        verbose_name_plural = "Question Paper Templates"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_active:
            # Only one active template is allowed
            QuestionPaperTemplate.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)


class QuestionPaper(BaseModel):
    """
    Represents a full question paper for a specific subject in an exam.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
    ]

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='question_papers')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='question_papers')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='question_papers')
    semester = models.PositiveIntegerField()
    
    COMPONENT_CHOICES = [
        ('Internal 1', 'Internal 1'),
        ('Internal 2', 'Internal 2'),
    ]
    assessment_component = models.CharField(
        max_length=20, 
        choices=COMPONENT_CHOICES,
        default='Internal 1',
        verbose_name="Assessment Component",
        help_text="Only Internal 1 and Internal 2 are supported for Question Paper generation."
    )
    
    date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    
    total_marks = models.PositiveIntegerField(default=0)
    
    instructions = models.TextField(
        default="All questions compulsory.\nUse of scientific calculator is allowed.\nDraw neat and clean drawings/figure & assume suitable data if necessary.",
        verbose_name="Instructions"
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_question_papers'
    )

    class Meta:
        unique_together = ('exam', 'subject', 'program')
        ordering = ['-created_at']
        verbose_name = "Question Paper"
        verbose_name_plural = "Question Papers"

    def __str__(self):
        return f"{self.subject.code} - {self.exam.name} ({self.program.code})"


class Question(BaseModel):
    """
    Represents a single question in a Question Paper.
    """
    CO_CHOICES = [
        ('CO1', 'CO1'),
        ('CO2', 'CO2'),
        ('CO3', 'CO3'),
        ('CO4', 'CO4'),
        ('CO5', 'CO5'),
    ]
    
    BTL_CHOICES = [
        ('BTL1', 'BTL1 - Remembering'),
        ('BTL2', 'BTL2 - Understanding'),
        ('BTL3', 'BTL3 - Applying'),
        ('BTL4', 'BTL4 - Analyzing'),
        ('BTL5', 'BTL5 - Evaluating'),
        ('BTL6', 'BTL6 - Creating'),
    ]

    paper = models.ForeignKey(QuestionPaper, on_delete=models.CASCADE, related_name='questions')
    
    question_number = models.CharField(max_length=20, help_text="e.g., Q1, Q2")
    text = models.TextField(verbose_name="Question Text")
    marks = models.PositiveIntegerField(default=5, help_text="Hardcoded to 5 marks per question.")
    
    co_mapping = models.CharField(max_length=10, choices=CO_CHOICES, verbose_name="CO Mapping")
    btl_mapping = models.CharField(max_length=10, choices=BTL_CHOICES, verbose_name="BTL Mapping")
    
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = "Question"
        verbose_name_plural = "Questions"

    def __str__(self):
        return f"{self.question_number} - {self.paper.subject.code}"
