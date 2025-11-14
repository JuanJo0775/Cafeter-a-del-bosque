"""
Patrón FACADE - Interfaz simplificada para el sistema completo
"""
from apps.users.models import User
from apps.menu.models import Product
from apps.orders.services import OrderService
from apps.orders.patterns.state import OrderStateManager
from apps.kitchen.handlers import KitchenRouter
from apps.notifications.services import NotificationService
from apps.notifications.strategies import NotificationManager


class CafeteriaFacade:
    """
    Facade que proporciona interfaz única y simplificada
    para todas las operaciones del sistema
    """

    def __init__(self):
        self.order_service = OrderService()
        self.kitchen_router = KitchenRouter()
        self.notification_service = NotificationService()

    def realizar_pedido_completo(self, customer_id, table_number, items, mesero_id=None):
        """
        Operación completa: crear pedido, notificar cocina, enrutar a estaciones

        Args:
            customer_id: ID del cliente
            table_number: Número de mesa
            items: Lista de items [{'product_id': 1, 'quantity': 2, 'extras': {...}}]
            mesero_id: ID del mesero asignado (opcional)

        Returns:
            dict con resultado completo
        """
        try:
            # 1. Obtener usuario
            customer = User.objects.get(id=customer_id)
            mesero = None
            if mesero_id:
                mesero = User.objects.get(id=mesero_id)
                # Registrar mesero como observer
                NotificationService.register_waiter(mesero)

            # 2. Crear orden usando Builder
            order = self.order_service.create_order_with_builder(
                customer=customer,
                table_number=table_number,
                items=items,
                mesero=mesero
            )

            # 3. Avanzar a estado EN_PREPARACION (automáticamente notifica cocina)
            OrderStateManager.advance_order(order)

            # 4. Enrutar a estaciones de cocina
            assignments = self.kitchen_router.route_order(order)

            # 5. Notificación multi-canal (opcional)
            if mesero and mesero.email:
                NotificationManager.send_notification(
                    'console',
                    mesero.email,
                    f"Nueva orden #{order.id} asignada a mesa {table_number}"
                )

            return {
                'success': True,
                'order': {
                    'id': order.id,
                    'table': order.table_number,
                    'status': order.status,
                    'total': float(order.total_price),
                    'items_count': order.items.count()
                },
                'kitchen_assignments': assignments,
                'mesero': mesero.username if mesero else None
            }

        except User.DoesNotExist:
            return {'success': False, 'error': 'Usuario no encontrado'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def completar_orden(self, order_id):
        """
        Marcar orden como lista y notificar mesero

        Args:
            order_id: ID de la orden

        Returns:
            dict con resultado
        """
        try:
            from apps.orders.models import Order
            order = Order.objects.get(id=order_id)

            # Avanzar estado (automáticamente notifica mesero)
            OrderStateManager.advance_order(order)

            return {
                'success': True,
                'order_id': order.id,
                'status': order.status,
                'message': 'Orden lista para servir'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def entregar_orden(self, order_id):
        """
        Marcar orden como entregada

        Args:
            order_id: ID de la orden

        Returns:
            dict con resultado
        """
        try:
            from apps.orders.models import Order
            order = Order.objects.get(id=order_id)

            OrderStateManager.advance_order(order)

            return {
                'success': True,
                'order_id': order.id,
                'status': order.status,
                'message': 'Orden entregada exitosamente'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def cancelar_orden(self, order_id, reason="", user_id=None):
        """
        Cancelar orden completamente

        Args:
            order_id: ID de la orden
            reason: Razón de cancelación
            user_id: ID del usuario que cancela

        Returns:
            dict con resultado
        """
        try:
            user = None
            if user_id:
                user = User.objects.get(id=user_id)

            order = self.order_service.cancel_order(order_id, reason, user)

            return {
                'success': True,
                'order_id': order.id,
                'status': order.status,
                'message': 'Orden cancelada'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def obtener_estado_sistema(self):
        """
        Obtener vista general del estado del sistema

        Returns:
            dict con estado completo
        """
        from apps.orders.models import Order

        return {
            'ordenes_pendientes': Order.objects.filter(status='PENDIENTE').count(),
            'ordenes_en_preparacion': Order.objects.filter(status='EN_PREPARACION').count(),
            'ordenes_listas': Order.objects.filter(status='LISTO').count(),
            'estaciones_cocina': self.kitchen_router.get_station_status(),
            'total_ordenes_hoy': Order.objects.filter(
                created_at__date=self.get_today()
            ).count()
        }

    def get_today(self):
        """Obtener fecha de hoy"""
        from datetime import date
        return date.today()

    def obtener_menu_disponible(self):
        """Obtener menú disponible (usando cache proxy)"""
        from apps.core.cache_proxy import MenuProxy

        proxy = MenuProxy()
        return proxy.get_menu()