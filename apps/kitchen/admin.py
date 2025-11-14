"""
Admin para cocina
"""
from django.contrib import admin
from .models import KitchenStation, StationQueue


@admin.register(KitchenStation)
class KitchenStationAdmin(admin.ModelAdmin):
    list_display = ['name', 'station_type', 'is_active']
    list_filter = ['station_type', 'is_active']
    search_fields = ['name']
    list_editable = ['is_active']


@admin.register(StationQueue)
class StationQueueAdmin(admin.ModelAdmin):
    list_display = ['station', 'order', 'assigned_at', 'is_completed', 'completed_at']
    list_filter = ['is_completed', 'station', 'assigned_at']
    search_fields = ['order__id']
    readonly_fields = ['assigned_at']