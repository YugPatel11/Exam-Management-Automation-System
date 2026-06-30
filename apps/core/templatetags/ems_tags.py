"""
Custom template tags for the EMS system.
Provides role-checking, navigation helpers, and formatting utilities.
"""
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='has_role')
def has_role(user, role):
    """
    Check if a user has a specific role.
    Usage: {% if user|has_role:"admin" %}
    """
    if not user or not user.is_authenticated:
        return False
    return user.role == role


@register.filter(name='has_any_role')
def has_any_role(user, roles_str):
    """
    Check if a user has any of the specified roles (comma-separated).
    Usage: {% if user|has_any_role:"admin,exam_coordinator" %}
    """
    if not user or not user.is_authenticated:
        return False
    roles = [r.strip() for r in roles_str.split(',')]
    return user.role in roles


@register.simple_tag(takes_context=True)
def active_nav(context, url_name):
    """
    Returns 'active' CSS class if the current URL matches.
    Usage: {% active_nav 'dashboard:home' %}
    """
    request = context.get('request')
    if not request:
        return ''
    from django.urls import resolve
    try:
        current = resolve(request.path_info).url_name
        if current == url_name:
            return 'bg-teal-700/20 text-teal-300 border-r-2 border-teal-400'
    except Exception:
        pass
    return ''


@register.simple_tag(takes_context=True)
def active_nav_group(context, *url_prefixes):
    """
    Returns active class if current URL starts with any of the given prefixes.
    Usage: {% active_nav_group '/master-data/' '/exams/' %}
    """
    request = context.get('request')
    if not request:
        return ''
    path = request.path
    for prefix in url_prefixes:
        if path.startswith(prefix):
            return 'bg-teal-700/20 text-teal-300'
    return ''


@register.filter(name='role_display')
def role_display(role_value):
    """
    Convert role value to display-friendly text.
    Usage: {{ user.role|role_display }}
    """
    role_map = {
        'admin': 'Admin',
        'exam_coordinator': 'Exam Coordinator',
        'subject_coordinator': 'Subject Coordinator',
        'subject_faculty': 'Subject Faculty',
    }
    return role_map.get(role_value, role_value)


@register.filter(name='initials')
def initials(user):
    """
    Get user initials for avatar.
    Usage: {{ user|initials }}
    """
    if not user:
        return '?'
    first = user.first_name[:1].upper() if user.first_name else ''
    last = user.last_name[:1].upper() if user.last_name else ''
    if first and last:
        return f"{first}{last}"
    return user.username[:2].upper()


@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Get a dictionary item by key.
    Usage: {{ dict|get_item:key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None
