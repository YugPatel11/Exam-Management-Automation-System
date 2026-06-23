"""
Models for Question Paper Management.
"""
from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from apps.exams.models import Exam
from apps.master_data.models import Subject, Program


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
    
    date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    
    total_marks = models.PositiveIntegerField(default=0)
    
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
    paper = models.ForeignKey(QuestionPaper, on_delete=models.CASCADE, related_name='questions')
    
    question_number = models.CharField(max_length=20, help_text="e.g., Q1(a), Q2(b)")
    text = models.TextField(verbose_name="Question Text")
    marks = models.PositiveIntegerField()
    
    co_mapping = models.CharField(max_length=50, verbose_name="CO Mapping", help_text="e.g., CO1, CO2")
    btl_mapping = models.CharField(max_length=50, verbose_name="BTL Mapping", help_text="e.g., L1, L2, L3")
    
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = "Question"
        verbose_name_plural = "Questions"

    def __str__(self):
        return f"{self.question_number} - {self.paper.subject.code}"
