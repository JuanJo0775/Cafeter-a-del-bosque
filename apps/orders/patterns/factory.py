"""
Patrón FACTORY METHOD para crear órdenes según tipo
"""
from abc import ABC, abstractmethod
from apps.orders.models import Order, OrderItem


class OrderFactory(ABC):
    """Factory abstracto para crear órdenes"""

    @abstractmethod
    def create_order(self, customer, table_number, **kwargs):
        pass

    def add_items(self, order, items_data):
        """Método común para agregar items"""
        for item_data in items_data:
            item = OrderItem(
                order=order,
                product_id=item_data['product_id'],
                quantity=item_data.get('quantity', 1),
                extras=item_data.get('extras', {})
            )
            item.calculate_subtotal()
            item.save()

        order.calculate_total()
        return order


class DineInOrderFactory(OrderFactory):
    """Factory para órdenes en mesa"""

    def create_order(self, customer, table_number, mesero=None, **kwargs):
        order = Order.objects.create(
            customer=customer,
            table_number=table_number,
            mesero=mesero,
            special_instructions=kwargs.get('special_instructions', '')
        )
        return order


class TakeAwayOrderFactory(OrderFactory):
    """Factory para órdenes para llevar"""

    def create_order(self, customer, table_number=0, **kwargs):
        order = Order.objects.create(
            customer=customer,
            table_number=table_number,  # 0 para takeaway
            special_instructions=f"PARA LLEVAR. {kwargs.get('special_instructions', '')}"
        )
        return order


class DeliveryOrderFactory(OrderFactory):
    """Factory para órdenes a domicilio"""

    def create_order(self, customer, table_number=0, **kwargs):
        address = kwargs.get('delivery_address', 'No especificada')
        order = Order.objects.create(
            customer=customer,
            table_number=table_number,
            special_instructions=f"DOMICILIO: {address}. {kwargs.get('special_instructions', '')}"
        )
        return order


def get_order_factory(order_type):
    """Obtener factory según tipo de orden"""
    factories = {
        'dine_in': DineInOrderFactory(),
        'take_away': TakeAwayOrderFactory(),
        'delivery': DeliveryOrderFactory(),
    }
    return factories.get(order_type, DineInOrderFactory())