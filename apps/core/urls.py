"""
URLs para módulo core (Facade, Config, Cache)
"""
from django.urls import path
from .views import (
    RealizarPedidoCompletoView,
    CompletarOrdenView,
    EntregarOrdenView,
    EstadoSistemaView,
    ConfiguracionView,
    MenuCachedView,
    BuscarProductoView
)

app_name = 'core'

urlpatterns = [
    # Facade - Operaciones completas
    path('pedido/realizar/', RealizarPedidoCompletoView.as_view(), name='realizar-pedido'),
    path('pedido/<int:order_id>/completar/', CompletarOrdenView.as_view(), name='completar-orden'),
    path('pedido/<int:order_id>/entregar/', EntregarOrdenView.as_view(), name='entregar-orden'),
    path('estado/', EstadoSistemaView.as_view(), name='estado-sistema'),

    # Singleton - Configuración
    path('config/', ConfiguracionView.as_view(), name='configuracion'),

    # Proxy - Cache del menú
    path('menu/cached/', MenuCachedView.as_view(), name='menu-cached'),
    path('menu/buscar/', BuscarProductoView.as_view(), name='buscar-producto'),
]