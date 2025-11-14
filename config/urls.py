"""
URL Configuration for Cafe del Bosque
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('apps.users.urls')),
    path('api/menu/', include('apps.menu.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/kitchen/', include('apps.kitchen.urls')),
    path('api/core/', include('apps.core.urls')),
]