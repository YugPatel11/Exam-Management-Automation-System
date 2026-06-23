"""
DRF serializers for the accounts app.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data — used in API responses."""
    role_display = serializers.CharField(source='get_role_display_name', read_only=True)
    display_name = serializers.CharField(source='get_display_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'role', 'role_display', 'display_name', 'phone',
            'department', 'designation', 'employee_id',
            'is_active', 'is_active_staff', 'last_activity',
        ]
        read_only_fields = ['id', 'username', 'role', 'last_activity']


class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user serializer for dropdowns and references."""
    display_name = serializers.CharField(source='get_display_name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'display_name', 'role']
