"""
FACADE: Interfaz unificada y simplificada para todo el sistema
Integra todos los patrones y subsistemas
"""
from datetime import datetime

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
        self.kitchen_router = KitchenRouter()
        self.command_invoker = CommandInvoker()
        self.caretaker = get_caretaker()
        print("[FACADE] Sistema inicializado")

    # ========== OPERACIONES DE ÓRDENES ==========

    def crear_pedido_completo(self, customer_id, table_number, items, mesero_id=None, instructions=""):
        """
        Operación completa: crear pedido con todos los patrones integrados

        - Builder: construir orden
        - Command: encapsular creación
        - State: establecer estado inicial
        - Memento: guardar snapshot
        - Observer: notificar cocina
        - Chain: enrutar a estaciones

        Args:
            customer_id: ID del cliente
            table_number: número de mesa
            items: lista de items
            mesero_id: ID del mesero (opcional)
            instructions: instrucciones especiales

        Returns:
            dict con resultado completo
        """
        print(f"\n[FACADE] ========== CREAR PEDIDO COMPLETO ==========")

        try:
            # 1. Obtener usuarios
            customer = User.objects.get(id=customer_id)
            mesero = User.objects.get(id=mesero_id) if mesero_id else None

            # Registrar observers
            NotificationService.register_customer(customer)
            if mesero:
                NotificationService.register_waiter(mesero)

            # 2. Construir orden usando Builder + Director
            director = OrderDirector()
            builder = OrderBuilder()

            order = director.build_custom_order(
                customer=customer,
                table=table_number,
                items=items,
                mesero=mesero,
                instructions=instructions
            )

            print(f"[FACADE] ✓ Orden #{order.id} construida")

            # 3. Procesar con Template Method
            template = get_order_process_template('new')
            process_result = template.process_order(order)

            if not process_result['success']:
                return process_result

            # 4. Avanzar a EN_PREPARACION usando State
            OrderStateManager.advance_order(order)

            # 5. Enrutar a cocina usando Chain of Responsibility
            assignments = self.kitchen_router.route_order(order)

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

        - State: avanzar estado
        - Template Method: procesar
        - Observer: notificar mesero
        """
        print(f"\n[FACADE] ========== COMPLETAR ORDEN #{order_id} ==========")

        try:
            order = Order.objects.get(id=order_id)

            # Procesar con template
            template = get_order_process_template('ready')
            result = template.process_order(order)

            if result['success']:
                # Avanzar estado
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

        - State: avanzar a entregado
        - Template Method: procesar entrega
        - Observer: notificar cliente
        """
        print(f"\n[FACADE] ========== ENTREGAR ORDEN #{order_id} ==========")

        try:
            order = Order.objects.get(id=order_id)

            # Procesar con template
            template = get_order_process_template('delivered')
            result = template.process_order(order)

            if result['success']:
                # Avanzar estado
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

        - Command: encapsular cancelación
        - State: cambiar a cancelado
        - Template Method: procesar cancelación
        - Observer: notificar todos
        """
        print(f"\n[FACADE] ========== CANCELAR ORDEN #{order_id} ==========")

        try:
            order = Order.objects.get(id=order_id)
            user = User.objects.get(id=user_id) if user_id else None

            # Verificar si se puede cancelar
            if not OrderStateManager.can_cancel(order):
                return {
                    'success': False,
                    'error': f'No se puede cancelar orden en estado {order.status}'
                }

            # Procesar con template
            template = get_order_process_template('cancelled')
            result = template.process_order(order)

            if result['success']:
                # Ejecutar comando de cancelación
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

        - State: verificar estado
        -Command: agregar/remover items
        - Memento: guardar estado antes de editar
        - Observer: notificar modificación
        """
        print(f"\n[FACADE] ========== EDITAR ORDEN #{order_id} ==========")

        try:
            order = Order.objects.get(id=order_id)

            # Verificar si se puede editar
            if not OrderStateManager.can_edit(order):
                return {
                    'success': False,
                    'error': f'No se puede editar orden en estado {order.status}'
                }

            # Guardar snapshot antes de editar
            self.caretaker.save(order, tag="before_edit", reason="Antes de edición")

            # Editar instrucciones
            if new_instructions is not None:
                order.special_instructions = new_instructions
                order.save()

            # Editar items si se proporcionaron
            if new_items:
                from apps.orders.patterns.command import RemoveItemCommand, AddItemCommand

                # Remover items existentes
                for item in order.items.all():
                    command = RemoveItemCommand(order, item.id)
                    self.command_invoker.execute_command(command)

                # Agregar nuevos items
                for item_data in new_items:
                    command = AddItemCommand(
                        order,
                        item_data['product_id'],
                        item_data.get('quantity', 1),
                        item_data.get('extras', {})
                    )
                    self.command_invoker.execute_command(command)

            # Recalcular total
            order.calculate_total()

            # Notificar modificación
            NotificationService.notify_order_modified(order)

            # Guardar snapshot después de editar
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

        - Memento: obtener snapshots
        - Command: obtener historial de comandos
        """
        try:
            order = Order.objects.get(id=order_id)

            # Historial de mementos
            mementos = self.caretaker.get_history(order_id)

            # Historial de comandos
            commands = self.command_invoker.get_history()

            # Historial de cambios en BD
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

        Args:
            menu_type: 'standard', 'seasonal', 'quick'

        Returns:
            dict con menú completo
        """
        print(f"\n[FACADE] ========== OBTENER MENÚ ({menu_type}) ==========")

        try:
            # Obtener temporada actual desde Singleton
            from apps.menu.singletons.menu_singleton import get_menu_singleton
            menu_singleton = get_menu_singleton()
            current_season = menu_singleton.get_current_season()

            # Construir menú usando Template Method
            template = get_menu_build_template(menu_type)
            menu = template.build_menu(season=current_season)

            # Cachear usando Proxy
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

        Args:
            new_season: 'REGULAR', 'INVIERNO', 'VERANO', 'OTONIO', 'PRIMAVERA'
        """
        print(f"\n[FACADE] ========== CAMBIAR TEMPORADA ==========")

        try:
            # Actualizar singleton
            from apps.menu.singletons.menu_singleton import get_menu_singleton
            menu_singleton = get_menu_singleton()
            menu_singleton.set_season(new_season)

            # Invalidar cache del proxy
            from apps.core.cache_proxy import MenuProxy
            proxy = MenuProxy()
            proxy.invalidate_cache()

            # Obtener nuevo menú
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

        - Chain: estado de estaciones
        - Observer: notificaciones de cocina
        """
        print(f"\n[FACADE] ========== ESTADO DE COCINA ==========")

        try:
            # Estado de estaciones
            stations_status = self.kitchen_router.get_station_status()

            # Notificaciones de cocina
            kitchen_notifications = NotificationService.get_kitchen_notifications()

            # Órdenes en preparación
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

        Args:
            station_type: tipo de estación
            order_id: ID de la orden
        """
        print(f"\n[FACADE] ========== COMPLETAR ITEM EN ESTACIÓN ==========")

        try:
            success = self.kitchen_router.complete_station_item(station_type, order_id)

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

        Args:
            user_id: ID del usuario
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

        Args:
            recipient: destinatario
            message: mensaje
            channels: lista de canales
            priority: prioridad
        """
        result = NotificationManager.send_multi_channel(
            recipient=recipient,
            message=message,
            channels=channels or ['console'],
            priority=priority
        )

        return {
            'success': True,
            'results': result
        }

    # ========== OPERACIONES DE ESTADO DEL SISTEMA ==========

    def obtener_estado_sistema(self):
        """
        Obtener vista general completa del sistema
        """
        print(f"\n[FACADE] ========== ESTADO DEL SISTEMA ==========")

        try:
            from datetime import date

            # Estadísticas de órdenes
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

            # Estado de cocina
            kitchen_status = self.obtener_estado_cocina()

            # Estado de notificaciones
            notification_stats = NotificationService.get_service_stats()

            # Menú actual
            from apps.menu.singletons.menu_singleton import get_menu_singleton
            menu_singleton = get_menu_singleton()
            menu_info = menu_singleton.get_info()

            # Cache info
            from apps.core.cache_proxy import MenuProxy
            proxy = MenuProxy()
            cache_info = proxy.get_cache_info()

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

            # Info básica
            basic_info = {
                'id': order.id,
                'table': order.table_number,
                'status': order.status,
                'customer': order.customer.username,
                'mesero': order.mesero.username if order.mesero else None,
                'created_at': order.created_at.isoformat(),
                'total': float(order.total_price)
            }

            # Items con decoradores aplicados
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

            # Estado
            state_info = OrderStateManager.get_state_info(order)

            # Historial resumido
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
        Deshacer última acción usando Command
        """
        success = self.command_invoker.undo()

        return {
            'success': success,
            'message': 'Acción deshecha' if success else 'No hay acciones para deshacer'
        }

    def rehacer_accion(self):
        """
        Rehacer acción usando Command
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

        # Limpiar cache
        from apps.core.cache_proxy import MenuProxy
        proxy = MenuProxy()
        proxy.invalidate_cache()

        # Limpiar notificaciones
        NotificationService.clear_all_notifications()

        # Limpiar historial de comandos
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