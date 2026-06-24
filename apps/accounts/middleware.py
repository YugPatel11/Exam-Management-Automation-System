"""
Custom middleware for authentication and session management.
"""
from django.utils import timezone


class RoleMiddleware:
    """
    Attaches user role information to the request object
    for easy access in views and templates.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            request.user_role = request.user.role
            request.is_admin = request.user.role == 'admin' or request.user.is_superuser
            request.is_coordinator = request.user.role == 'exam_coordinator'
            request.is_subject_coordinator = request.user.role == 'subject_coordinator'
            request.is_faculty = request.user.role == 'subject_faculty'
        else:
            request.user_role = None
            request.is_admin = False
            request.is_coordinator = False
            request.is_subject_coordinator = False
            request.is_faculty = False

        response = self.get_response(request)
        return response


class LastActivityMiddleware:
    """
    Tracks the last activity timestamp of authenticated users.
    Updates only every 5 minutes to avoid excessive DB writes.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            now = timezone.now()
            last = request.user.last_activity

            # Update only if last activity was more than 5 minutes ago
            if not last or (now - last).seconds > 300:
                # Use update() to avoid triggering signals
                from django.contrib.auth import get_user_model
                get_user_model().objects.filter(
                    pk=request.user.pk
                ).update(last_activity=now)

        return response
