"""
Function-based view decorators for role-based access control.
"""
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def role_required(*allowed_roles):
    """
    Decorator that restricts access to users with specific roles.

    Usage:
        @role_required('admin', 'exam_coordinator')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            if request.user.role not in allowed_roles:
                raise PermissionDenied("You don't have permission to access this page.")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_func):
    """Restrict to Admin only."""
    return role_required('admin')(view_func)


def coordinator_required(view_func):
    """Restrict to Admin and Exam Coordinator."""
    return role_required('admin', 'exam_coordinator')(view_func)


def subject_coordinator_required(view_func):
    """Restrict to Admin, Exam Coordinator, and Subject Coordinator."""
    return role_required('admin', 'exam_coordinator', 'subject_coordinator')(view_func)
