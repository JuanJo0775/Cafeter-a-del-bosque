"""
URLs para módulo de usuarios
"""
from django.urls import path
from .views import UserListView, UserDetailView, WaiterListView, ChefListView

app_name = 'users'

urlpatterns = [
    path('', UserListView.as_view(), name='user-list'),
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('waiters/', WaiterListView.as_view(), name='waiter-list'),
    path('chefs/', ChefListView.as_view(), name='chef-list'),
]