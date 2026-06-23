"""
Audit and file tracking models.
Centralized audit trail and database text content storage.
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


class TextContent(TimeStampedModel):
    """
    Stores all generated content (question papers, reports, seating plans, etc.)
    as text directly in the database. No external file storage needed.
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

    title = models.CharField(max_length=255, verbose_name="Title")
    content_type = models.CharField(
        max_length=50,
        default='text',
        help_text='Content format: text, html, csv, json'
    )
    content = models.TextField(
        verbose_name="Content",
        help_text="The full text content stored in the database."
    )
    module = models.CharField(max_length=30, choices=MODULE_CHOICES, db_index=True)
    related_object_id = models.CharField(
        max_length=100, blank=True,
        help_text='ID of the related entity (exam, subject, etc.)'
    )
    related_model = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_contents',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Text Content'
        verbose_name_plural = 'Text Contents'

    def __str__(self):
        return f"{self.module} - {self.identifier}"


class NotificationLog(models.Model):
    """
    Logs all system notifications sent to users via Email or SMS.
    """
    NOTIFICATION_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('system', 'System/In-App'),
    ]
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification Log"
        verbose_name_plural = "Notification Logs"

    def __str__(self):
        return f"[{self.get_notification_type_display()}] {self.user.get_display_name()} - {self.subject}"
