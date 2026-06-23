"""
Core utility functions used across all EMS apps.
"""
from django.utils import timezone


def get_academic_year():
    """
    Returns the current academic year string.
    If current month >= July, academic year is current_year-next_year.
    Otherwise, academic year is prev_year-current_year.
    """
    now = timezone.now()
    if now.month >= 7:
        return f"{now.year}-{now.year + 1}"
    return f"{now.year - 1}-{now.year}"


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def truncate_string(value, max_length=50):
    """Truncate a string to max_length with ellipsis."""
    if not value:
        return ''
    if len(str(value)) <= max_length:
        return str(value)
    return str(value)[:max_length - 3] + '...'


def format_file_size(size_bytes):
    """Format bytes into a human-readable string."""
    if size_bytes == 0:
        return '0 B'
    units = ['B', 'KB', 'MB', 'GB']
    unit_index = 0
    size = float(size_bytes)
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    return f"{size:.1f} {units[unit_index]}"
