"""
Servicios para gestión de órdenes
"""
from .models import Order, OrderItem
from .patterns.factory import get_order_factory
from .patterns.builder import OrderBuilder
from .patterns.state import OrderStateManager
from .patterns.command import (
    CreateOrderCommand,
    UpdateOrderStatusCommand,
    CancelOrderCommand,
    CommandInvoker
)
from .patterns.memento import get_caretaker, OrderOriginator


class OrderService:
    """Servicio principal para gestión de órdenes"""

    def __init__(self):
        self.command_invoker = CommandInvoker()
        self.caretaker = get_caretaker()

    def create_order_with_factory(self, order_type, customer, items, **kwargs):
        """Crear orden usando Factory Method"""
        factory = get_order_factory(order_type)
        order = factory.create_order(
            customer=customer,
            table_number=kwargs.get('table_number', 1),
            mesero=kwargs.get('mesero'),
            **kwargs
        )

        # Agregar items
        factory.add_items(order, items)

        # Guardar snapshot inicial
        self.caretaker.save(order, tag="initial")

        return order

    def create_order_with_builder(self, customer, table_number, items, mesero=None, instructions=""):
        """Crear orden usando Builder"""
        builder = OrderBuilder()
        builder.set_customer(customer)
        builder.set_table(table_number)

        if mesero:
            builder.set_mesero(mesero)

        if instructions:
            builder.add_special_instructions(instructions)

        for item in items:
            builder.add_product(
                item['product_id'],
                item.get('quantity', 1),
                item.get('extras', {})
            )

        order = builder.build()

        # Guardar snapshot
        self.caretaker.save(order, tag="created")

        return order

    def create_order_with_command(self, customer, table_number, items, mesero=None):
        """Crear orden usando Command"""
        command = CreateOrderCommand(customer, table_number, items, mesero)
        order = self.command_invoker.execute_command(command)
        return order

    def advance_order(self, order_id):
        """Avanzar orden al siguiente estado"""
        try:
            order = Order.objects.get(id=order_id)

            # Guardar estado antes de cambiar
            self.caretaker.save(order, tag=f"before_{order.status}")

            # Avanzar estado
            OrderStateManager.advance_order(order)

            return order
        except Order.DoesNotExist:
            raise Exception(f"Orden {order_id} no encontrada")

    def cancel_order(self, order_id, reason="", user=None):
        """Cancelar orden usando Command"""
        try:
            order = Order.objects.get(id=order_id)
            command = CancelOrderCommand(order, reason, user)
            return self.command_invoker.execute_command(command)
        except Order.DoesNotExist:
            raise Exception(f"Orden {order_id} no encontrada")

    def get_order_history(self, order_id):
        """Obtener historial de mementos de una orden"""
        return self.caretaker.get_history(order_id)

    def restore_order_state(self, order_id, tag="initial"):
        """Restaurar orden a un estado anterior"""
        try:
            order = Order.objects.get(id=order_id)
            state = self.caretaker.restore(order, tag)

            if state:
                return {
                    'current_state': OrderOriginator(order).get_state_summary(),
                    'saved_state': state
                }
            return None
        except Order.DoesNotExist:
            raise Exception(f"Orden {order_id} no encontrada")

    def get_pending_orders(self):
        """Obtener órdenes pendientes"""
        return Order.objects.filter(status='PENDIENTE').order_by('-created_at')

    def get_in_preparation_orders(self):
        """Obtener órdenes en preparación"""
        return Order.objects.filter(status='EN_PREPARACION').order_by('created_at')

    def get_ready_orders(self):
        """Obtener órdenes listas"""
        return Order.objects.filter(status='LISTO').order_by('prepared_at')

    def get_order_details(self, order_id):
        """Obtener detalles completos de una orden"""
        try:
            order = Order.objects.get(id=order_id)
            return {
                'id': order.id,
                'customer': order.customer.username,
                'mesero': order.mesero.username if order.mesero else None,
                'table': order.table_number,
                'status': order.status,
                'total': float(order.total_price),
                'items': [
                    {
                        'product': item.product.name,
                        'quantity': item.quantity,
                        'unit_price': float(item.unit_price),
                        'extras': item.extras,
                        'subtotal': float(item.subtotal)
                    }
                    for item in order.items.all()
                ],
                'created_at': order.created_at.isoformat(),
                'special_instructions': order.special_instructions
            }
        except Order.DoesNotExist:
            return None