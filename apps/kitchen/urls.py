"""
URLs para módulo de cocina
"""
from django.urls import path
from .views import (
    RouteOrderView,
    StationStatusView,
    StationQueueView,
    CompleteStationItemView,
    ChainInfoView
)

app_name = 'kitchen'

urlpatterns = [
    # Enrutamiento
    path('route/<int:order_id>/', RouteOrderView.as_view(), name='route-order'),

    # Estado de estaciones
    path('status/', StationStatusView.as_view(), name='station-status'),
    path('queue/<str:station_type>/', StationQueueView.as_view(), name='station-queue'),

    # Completar items
    path('complete/<str:station_type>/<int:order_id>/', CompleteStationItemView.as_view(), name='complete-item'),

    # Info de la cadena
    path('chain/info/', ChainInfoView.as_view(), name='chain-info'),
]