"""
Audit and file tracking models.
Centralized audit trail and Google Drive file metadata storage.
"""
from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class AuditLog(TimeStampedModel):
    """
    Tracks all important user actions throughout the system.
    Used for compliance, debugging, and accountability.
    """
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('archive', 'Archive'),
        ('unarchive', 'Unarchive'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('import', 'Import'),
        ('export', 'Export'),
        ('generate', 'Generate'),
        ('lock', 'Lock'),
        ('unlock', 'Unlock'),
        ('submit', 'Submit'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('assign', 'Assign'),
        ('upload', 'Upload'),
        ('download', 'Download'),
        ('password_change', 'Password Change'),
        ('password_reset', 'Password Reset'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES, db_index=True)
    model_name = models.CharField(max_length=100, blank=True, db_index=True)
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        user_str = self.user.get_full_name() if self.user else 'System'
        return f"{user_str} — {self.get_action_display()} — {self.model_name} — {self.created_at:%Y-%m-%d %H:%M}"


class FileUpload(TimeStampedModel):
    """
    Stores metadata for files uploaded to Google Drive.
    Actual files live in Drive; only links and metadata are stored here.
    """
    MODULE_CHOICES = [
        ('question_paper', 'Question Paper'),
        ('seating_plan', 'Seating Plan'),
        ('duty_chart', 'Duty Chart'),
        ('marks_report', 'Marks Report'),
        ('schedule', 'Schedule'),
        ('analysis', 'Analysis Report'),
        ('general', 'General'),
    ]

    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50, help_text='e.g., pdf, xlsx')
    google_drive_file_id = models.CharField(max_length=255, blank=True)
    google_drive_link = models.URLField(max_length=500, blank=True)
    module = models.CharField(max_length=30, choices=MODULE_CHOICES, db_index=True)
    related_object_id = models.CharField(max_length=100, blank=True, help_text='ID of the related entity')
    related_model = models.CharField(max_length=100, blank=True)
    file_size = models.PositiveIntegerField(default=0, help_text='Size in bytes')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_files',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'File Upload'
        verbose_name_plural = 'File Uploads'

    def __str__(self):
        return f"{self.file_name} ({self.get_module_display()})"
