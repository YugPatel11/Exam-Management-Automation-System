"""
Custom User model for the EMS system.
Supports role-based access control with four distinct roles.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model with role-based access control.
    Extends Django's AbstractUser with role, phone, and department fields.
    """
    ROLE_ADMIN = 'admin'
    ROLE_EXAM_COORDINATOR = 'exam_coordinator'
    ROLE_SUBJECT_COORDINATOR = 'subject_coordinator'
    ROLE_SUBJECT_FACULTY = 'subject_faculty'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_EXAM_COORDINATOR, 'Exam Coordinator'),
        (ROLE_SUBJECT_COORDINATOR, 'Subject Coordinator'),
        (ROLE_SUBJECT_FACULTY, 'Subject Faculty'),
    ]

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default=ROLE_SUBJECT_FACULTY,
        db_index=True,
        help_text='User role determines access level and available features.',
    )
    phone = models.CharField(max_length=15, blank=True, verbose_name='Phone Number')
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    employee_id = models.CharField(max_length=50, blank=True, unique=True, null=True)
    is_active_staff = models.BooleanField(
        default=True,
        help_text='Designates whether this faculty/staff member is currently active.',
    )
    last_activity = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['first_name', 'last_name']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        full_name = self.get_full_name()
        return full_name if full_name else self.username

    def get_display_name(self):
        """Return full name or username as fallback."""
        full_name = self.get_full_name()
        return full_name if full_name else self.username

    def get_role_display_name(self):
        """Return human-readable role name."""
        return dict(self.ROLE_CHOICES).get(self.role, self.role)

    # --- Role check properties ---

    @property
    def is_admin_role(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_exam_coordinator(self):
        return self.role == self.ROLE_EXAM_COORDINATOR

    @property
    def is_subject_coordinator(self):
        return self.role == self.ROLE_SUBJECT_COORDINATOR

    @property
    def is_subject_faculty(self):
        return self.role == self.ROLE_SUBJECT_FACULTY

    @property
    def can_manage_master_data(self):
        """Admin and Exam Coordinator can manage master data."""
        return self.role in (self.ROLE_ADMIN, self.ROLE_EXAM_COORDINATOR)

    @property
    def can_manage_exams(self):
        """Admin and Exam Coordinator can manage exams."""
        return self.role in (self.ROLE_ADMIN, self.ROLE_EXAM_COORDINATOR)

    @property
    def can_view_all_data(self):
        """Admin and Exam Coordinator can see all data."""
        return self.role in (self.ROLE_ADMIN, self.ROLE_EXAM_COORDINATOR)

    def get_dashboard_url(self):
        """Return the appropriate dashboard URL for this user's role."""
        role_urls = {
            self.ROLE_ADMIN: '/dashboard/admin/',
            self.ROLE_EXAM_COORDINATOR: '/dashboard/coordinator/',
            self.ROLE_SUBJECT_COORDINATOR: '/dashboard/subject-coordinator/',
            self.ROLE_SUBJECT_FACULTY: '/dashboard/faculty/',
        }
        return role_urls.get(self.role, '/dashboard/')
