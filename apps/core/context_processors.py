"""
Context processors for global template variables.
"""
from apps.core.utils import get_academic_year


def global_context(request):
    """Add global variables available in all templates."""
    context = {
        'app_name': 'EMS',
        'app_full_name': 'Exam Management System',
        'academic_year': get_academic_year(),
    }

    if request.user.is_authenticated:
        context.update({
            'user_role': request.user.role,
            'user_role_display': request.user.get_role_display(),
        })

    return context
