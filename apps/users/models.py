"""
Modelo de usuarios con roles
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Usuario extendido con roles para el sistema de cafetería
    """

    ROLE_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('MESERO', 'Mesero'),
        ('COCINERO', 'Cocinero'),
        ('CLIENTE', 'Cliente'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='CLIENTE'
    )

    phone = models.CharField(max_length=15, blank=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def is_waiter(self):
        """Verificar si es mesero"""
        return self.role == 'MESERO'

    def is_chef(self):
        """Verificar si es cocinero"""
        return self.role == 'COCINERO'

    def is_customer(self):
        """Verificar si es cliente"""
        return self.role == 'CLIENTE'