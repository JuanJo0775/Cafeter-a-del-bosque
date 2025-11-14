"""
URLs para módulo de órdenes
"""
from django.urls import path
from .views import (
    CreateOrderView,
    AdvanceOrderView,
    CancelOrderView,
    OrderHistoryView,
    OrderDetailView,
    OrderListView
)

app_name = 'orders'

urlpatterns = [
    # Listado y creación
    path('', OrderListView.as_view(), name='order-list'),
    path('create/', CreateOrderView.as_view(), name='create-order'),

    # Operaciones sobre órdenes específicas
    path('<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),
    path('<int:order_id>/advance/', AdvanceOrderView.as_view(), name='advance-order'),
    path('<int:order_id>/cancel/', CancelOrderView.as_view(), name='cancel-order'),
    path('<int:order_id>/history/', OrderHistoryView.as_view(), name='order-history'),
]