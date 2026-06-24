"""
View mixins for role-based access control and common patterns.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    CBV mixin that restricts access to users with specific roles.

    Usage:
        class MyView(RoleRequiredMixin, TemplateView):
            allowed_roles = ['admin', 'exam_coordinator']
    """
    allowed_roles = []

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        if self.request.user.is_superuser:
            return True
        if not self.allowed_roles:
            return True
        return self.request.user.role in self.allowed_roles

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('accounts:login')
        raise PermissionDenied("You don't have permission to access this page.")


class AdminRequiredMixin(RoleRequiredMixin):
    """Restrict access to Admin only."""
    allowed_roles = ['admin']


class ExamCoordinatorRequiredMixin(RoleRequiredMixin):
    """Restrict access to Admin and Exam Coordinator."""
    allowed_roles = ['admin', 'exam_coordinator']


class SubjectCoordinatorRequiredMixin(RoleRequiredMixin):
    """Restrict access to Admin, Exam Coordinator, and Subject Coordinator."""
    allowed_roles = ['admin', 'exam_coordinator', 'subject_coordinator']


class FacultyRequiredMixin(RoleRequiredMixin):
    """Allow all authenticated roles (Faculty and above)."""
    allowed_roles = ['admin', 'exam_coordinator', 'subject_coordinator', 'subject_faculty']


class AjaxResponseMixin:
    """
    Mixin to return JSON responses for AJAX requests
    and normal responses for regular requests.
    """

    def is_ajax(self):
        return self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'
