from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for the EMS User model."""
    list_display = ['username', 'first_name', 'last_name', 'email', 'role',
                    'department', 'is_active', 'is_active_staff', 'last_activity']
    list_filter = ['role', 'is_active', 'is_active_staff', 'department']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'employee_id']
    ordering = ['first_name', 'last_name']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('EMS Profile', {
            'fields': ('role', 'phone', 'department', 'designation',
                       'employee_id', 'is_active_staff', 'last_activity'),
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('EMS Profile', {
            'fields': ('first_name', 'last_name', 'email', 'role',
                       'phone', 'department', 'designation', 'employee_id'),
        }),
    )
