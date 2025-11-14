"""
URLs para módulo de cocina
"""
from django.urls import path
from .views import RouteOrderView, StationStatusView

app_name = 'kitchen'

urlpatterns = [
    path('route/<int:order_id>/', RouteOrderView.as_view(), name='route-order'),
    path('status/', StationStatusView.as_view(), name='station-status'),
]