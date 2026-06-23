"""
Base abstract models used across all EMS apps.
Provides consistent timestamps, archiving, and soft-delete patterns.
"""
import uuid
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Abstract model with automatic created/updated timestamps."""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']


class ArchivableModel(models.Model):
    """Abstract model with soft-archive capability."""
    is_archived = models.BooleanField(default=False, db_index=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(
        'accounts.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(class)s_archived',
    )

    class Meta:
        abstract = True

    def archive(self, user=None):
        """Soft-archive the record."""
        self.is_archived = True
        self.archived_at = timezone.now()
        self.archived_by = user
        self.save(update_fields=['is_archived', 'archived_at', 'archived_by'])

    def unarchive(self):
        """Restore an archived record."""
        self.is_archived = False
        self.archived_at = None
        self.archived_by = None
        self.save(update_fields=['is_archived', 'archived_at', 'archived_by'])


class BaseModel(TimeStampedModel, ArchivableModel):
    """
    Base model combining timestamps and archivability.
    Use this as the parent for most EMS entity models.
    """

    class Meta:
        abstract = True
        ordering = ['-created_at']


class UUIDModel(BaseModel):
    """Base model with UUID primary key instead of auto-increment."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
