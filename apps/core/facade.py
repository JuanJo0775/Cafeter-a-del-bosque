"""
FACADE: Interfaz unificada y simplificada para todo el sistema
Integra todos los patrones y subsistemas
"""
from datetime import datetime

# Añadido para mejoras SIN eliminar nada
from apps.core.service_registry import get_registry

from apps.users.models import User
from apps.menu.models import Product
from apps.orders.models import Order
from apps.orders.patterns.builder import OrderBuilder, OrderDirector
from apps.orders.patterns.state import OrderStateManager
from apps.orders.patterns.command import CommandInvoker, CreateOrderCommand, CancelOrderCommand
from apps.orders.patterns.memento import get_caretaker
from apps.kitchen.handlers import KitchenRouter
from apps.notifications.services import NotificationService
from apps.notifications.strategies import NotificationManager
from apps.core.templates.order_template import get_order_process_template
from apps.core.templates.menu_template import get_menu_build_template


class CafeteriaFacade:
    """
    Facade principal que simplifica acceso a todo el sistema
    Oculta la complejidad interna y proporciona interfaz unificada
    """

    def __init__(self):
        # 🔹 Integración con registry, sin eliminar tu lógica
        registry = get_registry()

        # Mantengo tus instancias, agrego opción de obtenerlas del registry
        self.kitchen_router = registry.kitchen if hasattr(registry, "kitchen") else KitchenRouter()
        self.command_invoker = registry.orders.command_invoker if hasattr(registry, "orders") else CommandInvoker()

        self.caretaker = get_caretaker()
        print("[FACADE] Sistema inicializado")

    # ========== OPERACIONES DE ÓRDENES ==========

    def crear_pedido_completo(self, customer_id=None, customer_name="", table_number=None, items=None, mesero_id=None, instructions=""):
        """
        Operación completa: crear pedido con todos los patrones integrados
        """
        print(f"\n[FACADE] ========== CREAR PEDIDO COMPLETO ==========")

        try:
            # 1. Obtener usuarios
            # Soporte para cliente NO registrado
            if customer_id:
                customer = User.objects.get(id=customer_id)
            else:
                customer = None

            mesero = User.objects.get(id=mesero_id) if mesero_id else None

            # Registrar observers
            NotificationService.register_customer(customer)
            if mesero:
                NotificationService.register_waiter(mesero)

            # 2. Builder
            director = OrderDirector()
            builder = OrderBuilder()

            order = director.build_custom_order(
                customer=customer,
                customer_name=customer_name,
                table=table_number,
                items=items,
                mesero=mesero,
                instructions=instructions
            )

            print(f"[FACADE] ✓ Orden #{order.id} construida")

            # 3. Template Method
            template = get_order_process_template('new')
            process_result = template.process_order(order)

            if not process_result['success']:
                return process_result

            # 4. State
            OrderStateManager.advance_order(order)

            # 5. Chain of Responsibility (Kitchen)
            registry = get_registry()
            kitchen = registry.kitchen if hasattr(registry, "kitchen") else self.kitchen_router
            assignments = kitchen.route_order(order)

            print(f"[FACADE] ========== PEDIDO COMPLETADO ==========\n")

            return {
                'success': True,
                'order': {
                    'id': order.id,
                    'table': order.table_number,
                    'status': order.status,
                    'total': float(order.total_price),
                    'items_count': order.items.count(),
                    'customer': customer.username,
                    'mesero': mesero.username if mesero else None
                },
                'kitchen_assignments': assignments,
                'process_result': process_result
            }

        except User.DoesNotExist:
            return {'success': False, 'error': 'Usuario no encontrado'}
        except Exception as e:
            print(f"[FACADE] ✗ Error: {e}")
            return {'success': False, 'error': str(e)}

    def completar_orden(self, order_id):
        """
        Marcar orden como LISTA
        """
        print(f"\n[FACADE] ========== COMPLETAR ORDEN #{order_id} ==========")

        try:
            order = Order.objects.get(id=order_id)

            # Template Method
            template = get_order_process_template('ready')
            result = template.process_order(order)

            if result['success']:
                OrderStateManager.advance_order(order)
                print(f"[FACADE] ========== ORDEN COMPLETADA ==========\n")

            return {
                'success': result['success'],
                'order_id': order.id,
                'status': order.status,
                'message': 'Orden lista para servir'
            }

        except Order.DoesNotExist:
            return {'success': False, 'error': 'Orden no encontrada'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def entregar_orden(self, order_id):
        """
        Marcar orden como ENTREGADA
        """
        print(f"\n[FACADE] ========== ENTREGAR ORDEN #{order_id} ==========")

        try:
            order = Order.objects.get(id=order_id)

            template = get_order_process_template('delivered')
            result = template.process_order(order)

            if result['success']:
                OrderStateManager.advance_order(order)
                print(f"[FACADE] ========== ORDEN ENTREGADA ==========\n")

            return {
                'success': result['success'],
                'order_id': order.id,
                'status': order.status,
                'message': 'Orden entregada exitosamente'
            }

        except Order.DoesNotExist:
            return {'success': False, 'error': 'Orden no encontrada'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def cancelar_orden(self, order_id, reason="", user_id=None):
        """
        Cancelar orden completa
        """
        print(f"\n[FACADE] ========== CANCELAR ORDEN #{order_id} ==========")

        try:
            order = Order.objects.get(id=order_id)
            user = User.objects.get(id=user_id) if user_id else None

            if not OrderStateManager.can_cancel(order):
                return {
                    'success': False,
                    'error': f'No se puede cancelar orden en estado {order.status}'
                }

            template = get_order_process_template('cancelled')
            result = template.process_order(order)

            if result['success']:
                command = CancelOrderCommand(order, reason, user)
                self.command_invoker.execute_command(command)

                print(f"[FACADE] ========== ORDEN CANCELADA ==========\n")

            return {
                'success': result['success'],
                'order_id': order.id,
                'status': order.status,
                'reason': reason,
                'message': 'Orden cancelada'
            }

        except Order.DoesNotExist:
            return {'success': False, 'error': 'Orden no encontrada'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def editar_orden(self, order_id, new_items=None, new_instructions=None):
        """
        Editar orden (solo si está PENDIENTE)
        """
        print(f"\n[FACADE] ========== EDITAR ORDEN #{order_id} ==========")

        try:
            order = Order.objects.get(id=order_id)

            if not OrderStateManager.can_edit(order):
                return {
                    'success': False,
                    'error': f'No se puede editar orden en estado {order.status}'
                }

            self.caretaker.save(order, tag="before_edit", reason="Antes de edición")

            if new_instructions is not None:
                order.special_instructions = new_instructions
                order.save()

            if new_items:
                from apps.orders.patterns.command import RemoveItemCommand, AddItemCommand
                for item in order.items.all():
                    self.command_invoker.execute_command(RemoveItemCommand(order, item.id))

                for item_data in new_items:
                    self.command_invoker.execute_command(
                        AddItemCommand(
                            order,
                            item_data['product_id'],
                            item_data.get('quantity', 1),
                            item_data.get('extras', {})
                        )
                    )

            order.calculate_total()

            NotificationService.notify_order_modified(order)

            self.caretaker.save(order, tag="after_edit", reason="Después de edición")

            print(f"[FACADE] ========== ORDEN EDITADA ==========\n")

            return {
                'success': True,
                'order_id': order.id,
                'status': order.status,
                'total': float(order.total_price),
                'items_count': order.items.count(),
                'message': 'Orden editada exitosamente'
            }

        except Order.DoesNotExist:
            return {'success': False, 'error': 'Orden no encontrada'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def obtener_historial_orden(self, order_id):
        """
        Obtener historial completo de una orden
        """
        try:
            order = Order.objects.get(id=order_id)
            mementos = self.caretaker.get_history(order_id)
            commands = self.command_invoker.get_history()

            from apps.orders.models import OrderHistory
            db_history = OrderHistory.objects.filter(order=order).order_by('-timestamp')

            return {
                'success': True,
                'order_id': order_id,
                'mementos': mementos,
                'commands': commands,
                'database_history': list(db_history.values(
                    'action', 'previous_status', 'new_status',
                    'changed_by__username', 'reason', 'timestamp'
                ))
            }

        except Order.DoesNotExist:
            return {'success': False, 'error': 'Orden no encontrada'}

    # ========== OPERACIONES DE MENÚ ==========

    def obtener_menu_actual(self, menu_type='standard'):
        """
        Obtener menú actual usando Singleton + Template Method + Proxy
        """
        print(f"\n[FACADE] ========== OBTENER MENÚ ({menu_type}) ==========")

        try:
            from apps.menu.singletons.menu_singleton import get_menu_singleton
            menu_singleton = get_menu_singleton()
            current_season = menu_singleton.get_current_season()

            template = get_menu_build_template(menu_type)
            menu = template.build_menu(season=current_season)

            # 🔹 Usar registry.menu si tiene proxy interno
            registry = get_registry()
            menu_service = getattr(registry, "menu", None)

            if menu_service and hasattr(menu_service, "get_cache_info"):
                cache_info = menu_service.get_cache_info()
            else:
                # fallback: tu implementación original
                from apps.core.cache_proxy import MenuProxy
                proxy = MenuProxy()
                cache_info = proxy.get_cache_info()

            print(f"[FACADE] ========== MENÚ OBTENIDO ==========\n")

            return {
                'success': True,
                'menu': menu,
                'cache_info': cache_info,
                'season': current_season
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def cambiar_temporada(self, new_season):
        """
        Cambiar temporada del menú usando Singleton + Strategy
        """
        print(f"\n[FACADE] ========== CAMBIAR TEMPORADA ==========")

        try:
            from apps.menu.singletons.menu_singleton import get_menu_singleton
            menu_singleton = get_menu_singleton()
            menu_singleton.set_season(new_season)

            registry = get_registry()
            menu_service = getattr(registry, "menu", None)

            if menu_service and hasattr(menu_service, "invalidate_cache"):
                menu_service.invalidate_cache()
            else:
                from apps.core.cache_proxy import MenuProxy
                MenuProxy().invalidate_cache()

            menu = menu_singleton.get_complete_menu()

            print(f"[FACADE] ========== TEMPORADA CAMBIADA ==========\n")

            return {
                'success': True,
                'new_season': new_season,
                'menu': menu
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== OPERACIONES DE COCINA ==========

    def obtener_estado_cocina(self):
        """
        Obtener estado completo de cocina
        """
        print(f"\n[FACADE] ========== ESTADO DE COCINA ==========")

        try:
            registry = get_registry()
            kitchen = registry.kitchen if hasattr(registry, "kitchen") else self.kitchen_router

            stations_status = kitchen.get_station_status()
            kitchen_notifications = NotificationService.get_kitchen_notifications()
            orders_in_prep = Order.objects.filter(status='EN_PREPARACION').count()

            print(f"[FACADE] ========== ESTADO OBTENIDO ==========\n")

            return {
                'success': True,
                'stations': stations_status,
                'total_stations': len(stations_status),
                'orders_in_preparation': orders_in_prep,
                'notifications_count': len(kitchen_notifications),
                'active_notifications': [
                    n for n in kitchen_notifications
                    if not n.get('read', False)
                ]
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def completar_item_estacion(self, station_type, order_id):
        """
        Marcar item como completado en una estación
        """
        print(f"\n[FACADE] ========== COMPLETAR ITEM EN ESTACIÓN ==========")

        try:
            registry = get_registry()
            kitchen = registry.kitchen if hasattr(registry, "kitchen") else self.kitchen_router

            success = kitchen.complete_station_item(station_type, order_id)

            if success:
                print(f"[FACADE] ========== ITEM COMPLETADO ==========\n")
                return {
                    'success': True,
                    'station_type': station_type,
                    'order_id': order_id,
                    'message': 'Item completado en estación'
                }
            else:
                return {
                    'success': False,
                    'error': 'No se pudo completar item'
                }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== OPERACIONES DE NOTIFICACIONES ==========

    def obtener_notificaciones_usuario(self, user_id):
        """
        Obtener notificaciones de un usuario
        """
        try:
            user = User.objects.get(id=user_id)

            if user.role == 'MESERO':
                notifications = NotificationService.get_waiter_notifications(user)
            elif user.role == 'COCINERO':
                notifications = NotificationService.get_chef_notifications(user)
            elif user.role == 'CLIENTE':
                notifications = NotificationService.get_customer_notifications(user)
            else:
                notifications = []

            return {
                'success': True,
                'user_id': user.id,
                'username': user.username,
                'role': user.role,
                'notifications': notifications,
                'total': len(notifications),
                'unread': len([n for n in notifications if not n.get('read', False)])
            }

        except User.DoesNotExist:
            return {'success': False, 'error': 'Usuario no encontrado'}

    def enviar_notificacion_personalizada(self, recipient, message, channels=None, priority='normal'):
        """
        Enviar notificación usando Strategy
        """
        result = NotificationManager.send_multi_channel(
            recipient=recipient,
            message=message,
            channels=channels or ['console'],
            priority=priority
        )

        return {'success': True, 'results': result}

    # ========== OPERACIONES DE ESTADO DEL SISTEMA ==========

    def obtener_estado_sistema(self):
        """
        Obtener vista general del sistema
        """
        print(f"\n[FACADE] ========== ESTADO DEL SISTEMA ==========")

        try:
            from datetime import date

            orders_stats = {
                'pendientes': Order.objects.filter(status='PENDIENTE').count(),
                'en_preparacion': Order.objects.filter(status='EN_PREPARACION').count(),
                'listas': Order.objects.filter(status='LISTO').count(),
                'entregadas_hoy': Order.objects.filter(
                    status='ENTREGADO',
                    delivered_at__date=date.today()
                ).count(),
                'canceladas_hoy': Order.objects.filter(
                    status='CANCELADO',
                    created_at__date=date.today()
                ).count()
            }

            kitchen_status = self.obtener_estado_cocina()
            notification_stats = NotificationService.get_service_stats()

            from apps.menu.singletons.menu_singleton import get_menu_singleton
            menu_singleton = get_menu_singleton()
            menu_info = menu_singleton.get_info()

            # 🔹 Integración con registry para cache
            registry = get_registry()
            menu_service = getattr(registry, "menu", None)

            if menu_service and hasattr(menu_service, "get_cache_info"):
                cache_info = menu_service.get_cache_info()
            else:
                from apps.core.cache_proxy import MenuProxy
                cache_info = MenuProxy().get_cache_info()

            print(f"[FACADE] ========== ESTADO OBTENIDO ==========\n")

            return {
                'success': True,
                'orders': orders_stats,
                'kitchen': kitchen_status,
                'notifications': notification_stats,
                'menu': menu_info,
                'cache': cache_info,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def obtener_resumen_orden(self, order_id):
        """
        Obtener resumen completo de una orden
        """
        try:
            order = Order.objects.get(id=order_id)

            basic_info = {
                'id': order.id,
                'table': order.table_number,
                'status': order.status,
                'customer': order.customer.username,
                'mesero': order.mesero.username if order.mesero else None,
                'created_at': order.created_at.isoformat(),
                'total': float(order.total_price)
            }

            items = []
            for item in order.items.all():
                from apps.menu.decorators.product_decorator import DecoratorFactory
                decorated_info = DecoratorFactory.get_decorated_info(item.product, item.extras)

                items.append({
                    'product': item.product.name,
                    'quantity': item.quantity,
                    'decorated_name': decorated_info['name'],
                    'unit_price': float(item.unit_price),
                    'subtotal': float(item.subtotal),
                    'extras': item.extras
                })

            state_info = OrderStateManager.get_state_info(order)
            history = self.caretaker.get_history(order_id)

            return {
                'success': True,
                'basic_info': basic_info,
                'items': items,
                'state_info': state_info,
                'history_snapshots': len(history),
                'latest_snapshot': self.caretaker.get_latest(order_id)
            }

        except Order.DoesNotExist:
            return {'success': False, 'error': 'Orden no encontrada'}

    # ========== UTILIDADES ==========

    def deshacer_ultima_accion(self):
        """
        Deshacer última acción
        """
        success = self.command_invoker.undo()
        return {
            'success': success,
            'message': 'Acción deshecha' if success else 'No hay acciones para deshacer'
        }

    def rehacer_accion(self):
        """
        Rehacer acción
        """
        success = self.command_invoker.redo()
        return {
            'success': success,
            'message': 'Acción rehecha' if success else 'No hay acciones para rehacer'
        }

    def limpiar_sistema(self):
        """
        Limpiar caches, notificaciones y datos temporales
        """
        print(f"\n[FACADE] ========== LIMPIANDO SISTEMA ==========")

        # Cache
        registry = get_registry()
        menu_service = getattr(registry, "menu", None)

        if menu_service and hasattr(menu_service, "invalidate_cache"):
            menu_service.invalidate_cache()
        else:
            from apps.core.cache_proxy import MenuProxy
            MenuProxy().invalidate_cache()

        # Notificaciones
        NotificationService.clear_all_notifications()

        # Historial de comandos
        self.command_invoker.clear_history()

        print(f"[FACADE] ========== SISTEMA LIMPIADO ==========\n")

        return {
            'success': True,
            'message': 'Sistema limpiado exitosamente'
        }


# Singleton del Facade
_facade_instance = None


def get_facade():
    """Obtener instancia única del Facade"""
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = CafeteriaFacade()
    return _facade_instance
