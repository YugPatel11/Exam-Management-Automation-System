"""
Models for Reports Management.
"""
from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from apps.core.models_audit import TextContent
from apps.exams.models import Exam


class Report(BaseModel):
    """
    Stores generated reports as text content in the database.
    Replaces external storage like Google Drive.
    """
    REPORT_TYPES = [
        ('seating_arrangement', 'Seating Arrangement'),
        ('duty_chart', 'Duty Chart'),
        ('marks_summary', 'Marks Summary'),
        ('result_analysis', 'Result Analysis'),
        ('exam_schedule', 'Exam Schedule'),
        ('question_paper', 'Question Paper'),
    ]

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    
    # Store the actual report content as text (HTML/Markdown/CSV format)
    content = models.OneToOneField(TextContent, on_delete=models.CASCADE)
    
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Report"
        verbose_name_plural = "Reports"

    def __str__(self):
        return f"{self.get_report_type_display()} for {self.exam.name}"
