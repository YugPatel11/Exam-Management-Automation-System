"""
Audit logging service.
Centralized function for recording audit trail entries.
"""
from apps.core.utils import get_client_ip


def log_action(request=None, user=None, action='', model_name='', object_id='',
               object_repr='', details=None):
    """
    Create an audit log entry.

    Args:
        request: The HTTP request (optional, used for IP/user-agent)
        user: The user performing the action
        action: Action type (create, update, delete, etc.)
        model_name: Name of the model being acted upon
        object_id: ID of the specific object
        object_repr: String representation of the object
        details: Dict of additional details
    """
    from apps.core.models_audit import AuditLog

    ip_address = None
    user_agent = ''

    if request:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if not user:
            user = request.user if request.user.is_authenticated else None

    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=str(object_id) if object_id else '',
        object_repr=str(object_repr)[:255] if object_repr else '',
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent[:500] if user_agent else '',
    )
