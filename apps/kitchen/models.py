"""
Modelos para estaciones de cocina
"""
from datetime import datetime

from django.db import models
from apps.orders.models import Order


class KitchenStation(models.Model):
    """Estación de cocina - para Chain of Responsibility"""

    STATION_TYPES = [
        ('BEBIDAS_CALIENTES', 'Bebidas Calientes'),
        ('BEBIDAS_FRIAS', 'Bebidas Frías'),
        ('PANADERIA', 'Panadería'),
        ('COCINA', 'Cocina Principal'),
        ('POSTRES', 'Postres'),
    ]

    name = models.CharField(max_length=100)
    station_type = models.CharField(max_length=30, choices=STATION_TYPES)
    is_active = models.BooleanField(default=True)
    can_handle_categories = models.JSONField(
        default=list,
        help_text="Lista de category_types que puede manejar: ['BEBIDAS', 'POSTRES']"
    )

    class Meta:
        db_table = 'kitchen_stations'
        verbose_name = 'Estación de Cocina'
        verbose_name_plural = 'Estaciones de Cocina'

    def __str__(self):
        return f"{self.name} ({self.get_station_type_display()})"


class StationQueue(models.Model):
    """Cola de órdenes en una estación"""

    station = models.ForeignKey(KitchenStation, on_delete=models.CASCADE, related_name='queue')
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        db_table = 'station_queue'
        verbose_name = 'Cola de Estación'
        verbose_name_plural = 'Colas de Estaciones'
        ordering = ['assigned_at']

    def __str__(self):
        return f"{self.station.name} - Orden #{self.order.id}"

    def mark_completed(self):
        """Marcar como completado"""
        self.is_completed = True
        self.completed_at = datetime.now()
        self.save()
        print(f"[QUEUE] Item completado: Orden #{self.order.id} en {self.station.name}")

    def get_waiting_time(self):
        """Calcular tiempo de espera"""
        if self.is_completed and self.completed_at:
            delta = self.completed_at - self.assigned_at
            return int(delta.total_seconds() / 60)  # minutos
        else:
            delta = datetime.now() - self.assigned_at
            return int(delta.total_seconds() / 60)  # minutos

    def is_delayed(self, threshold_minutes=30):
        """Verificar si está retrasado"""
        if not self.is_completed:
            waiting_time = self.get_waiting_time()
            return waiting_time > threshold_minutes
        return False

    class Meta:
        db_table = 'station_queue'
        verbose_name = 'Cola de Estación'
        verbose_name_plural = 'Colas de Estaciones'
        ordering = ['assigned_at']

    def __str__(self):
        status = "✓" if self.is_completed else "⏳"
        return f"{status} {self.station.name} - Orden #{self.order.id}"