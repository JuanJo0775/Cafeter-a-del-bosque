"""
URLs para módulo de notificaciones
"""
from django.urls import path
from .views import (
    RegisterObserverView,
    UnregisterObserverView,
    GetNotificationsView,
    GetKitchenNotificationsView,
    SendNotificationView,
    SendMultiChannelNotificationView,
    ServiceStatsView,
    AvailableStrategiesView,
    TestStrategyView,
    ClearNotificationsView
)

app_name = 'notifications'

urlpatterns = [
    # Gestión de observers
    path('register/', RegisterObserverView.as_view(), name='register-observer'),
    path('unregister/', UnregisterObserverView.as_view(), name='unregister-observer'),

    # Obtener notificaciones
    path('user/<int:user_id>/', GetNotificationsView.as_view(), name='user-notifications'),
    path('kitchen/', GetKitchenNotificationsView.as_view(), name='kitchen-notifications'),

    # Enviar notificaciones
    path('send/', SendNotificationView.as_view(), name='send-notification'),
    path('send/multi/', SendMultiChannelNotificationView.as_view(), name='send-multi-channel'),

    # Estadísticas y utilidades
    path('stats/', ServiceStatsView.as_view(), name='service-stats'),
    path('strategies/', AvailableStrategiesView.as_view(), name='available-strategies'),
    path('test/', TestStrategyView.as_view(), name='test-strategy'),
    path('clear/', ClearNotificationsView.as_view(), name='clear-notifications'),
]