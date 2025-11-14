"""
Serializers para usuarios
"""
from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer básico para usuarios"""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone']
        read_only_fields = ['id']


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para usuarios"""

    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'role_display', 'phone', 'date_joined', 'is_active'
        ]
        read_only_fields = ['id', 'date_joined']