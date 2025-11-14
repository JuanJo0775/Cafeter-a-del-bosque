"""
Admin para órdenes
"""
from django.contrib import admin
from .models import Order, OrderItem, OrderHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['subtotal']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'mesero', 'table_number', 'status', 'total_price', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['customer__username', 'mesero__username']
    readonly_fields = ['created_at', 'prepared_at', 'delivered_at', 'total_price']
    inlines = [OrderItemInline]

    fieldsets = (
        ('Información Básica', {
            'fields': ('customer', 'mesero', 'table_number', 'status')
        }),
        ('Detalles', {
            'fields': ('special_instructions', 'total_price')
        }),
        ('Fechas', {
            'fields': ('created_at', 'prepared_at', 'delivered_at')
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'unit_price', 'subtotal']
    list_filter = ['order__status']
    search_fields = ['product__name', 'order__id']
    readonly_fields = ['subtotal']


@admin.register(OrderHistory)
class OrderHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'action', 'previous_status', 'new_status', 'changed_by', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['order__id', 'reason']
    readonly_fields = ['timestamp']