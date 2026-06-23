from django.contrib import admin
from apps.core.models_audit import AuditLog, FileUpload


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'object_repr', 'created_at', 'ip_address']
    list_filter = ['action', 'model_name', 'created_at']
    search_fields = ['user__username', 'object_repr', 'model_name']
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'object_repr',
                       'details', 'ip_address', 'user_agent', 'created_at']
    ordering = ['-created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'file_type', 'module', 'uploaded_by', 'created_at']
    list_filter = ['file_type', 'module', 'created_at']
    search_fields = ['file_name', 'google_drive_file_id']
    readonly_fields = ['created_at', 'updated_at']
