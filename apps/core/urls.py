"""
URLs para módulo core (Facade integrado)
"""
from django.urls import path
from .views import (
    # Operaciones de órdenes
    RealizarPedidoCompletoView,
    CompletarOrdenView,
    EntregarOrdenView,
    CancelarOrdenView,
    EditarOrdenView,
    HistorialOrdenView,
    ResumenOrdenView,

    # Estado del sistema
    EstadoSistemaView,
    EstadoCocinaView,

    # Menú
    MenuActualView,
    CambiarTemporadaView,

    # Notificaciones
    NotificacionesUsuarioView,

    # Utilidades
    DeshacerAccionView,
    RehacerAccionView,
    LimpiarSistemaView
)

app_name = 'core'

urlpatterns = [
    # === OPERACIONES DE ÓRDENES ===
    path('pedido/crear/', RealizarPedidoCompletoView.as_view(), name='crear-pedido'),
    path('pedido/<int:order_id>/completar/', CompletarOrdenView.as_view(), name='completar-orden'),
    path('pedido/<int:order_id>/entregar/', EntregarOrdenView.as_view(), name='entregar-orden'),
    path('pedido/<int:order_id>/cancelar/', CancelarOrdenView.as_view(), name='cancelar-orden'),
    path('pedido/<int:order_id>/editar/', EditarOrdenView.as_view(), name='editar-orden'),
    path('pedido/<int:order_id>/historial/', HistorialOrdenView.as_view(), name='historial-orden'),
    path('pedido/<int:order_id>/resumen/', ResumenOrdenView.as_view(), name='resumen-orden'),

    # === ESTADO DEL SISTEMA ===
    path('estado/', EstadoSistemaView.as_view(), name='estado-sistema'),
    path('cocina/estado/', EstadoCocinaView.as_view(), name='estado-cocina'),

    # === MENÚ ===
    path('menu/actual/', MenuActualView.as_view(), name='menu-actual'),
    path('menu/temporada/', CambiarTemporadaView.as_view(), name='cambiar-temporada'),

    # === NOTIFICACIONES ===
    path('notificaciones/<int:user_id>/', NotificacionesUsuarioView.as_view(), name='notificaciones-usuario'),

    # === UTILIDADES ===
    path('undo/', DeshacerAccionView.as_view(), name='deshacer'),
    path('redo/', RehacerAccionView.as_view(), name='rehacer'),
    path('limpiar/', LimpiarSistemaView.as_view(), name='limpiar-sistema'),
]