"""
URLs para módulo de menú
"""
from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    # Listado de categorías y productos
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('products/', views.ProductListView.as_view(), name='products'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),

    # Menús por temporada (Abstract Factory)
    path('seasonal/<str:season>/', views.SeasonalMenuView.as_view(), name='seasonal-menu'),
    path('time-of-day/<str:time>/', views.TimeBasedMenuView.as_view(), name='time-menu'),
]