"""
Patrón BUILDER para construir órdenes complejas paso a paso
"""
from apps.orders.models import Order, OrderItem
from apps.menu.models import Product


class OrderBuilder:
    """
    Builder para construir órdenes paso a paso
    Permite agregar items, extras, instrucciones, etc.
    """

    def __init__(self):
        self._customer = None
        self._mesero = None
        self._table_number = 1
        self._items = []
        self._special_instructions = ""

    def set_customer(self, customer):
        """Establecer cliente"""
        self._customer = customer
        return self

    def set_mesero(self, mesero):
        """Establecer mesero"""
        self._mesero = mesero
        return self

    def set_table(self, table_number):
        """Establecer mesa"""
        self._table_number = table_number
        return self

    def add_product(self, product_id, quantity=1, extras=None):
        """
        Agregar producto a la orden

        Args:
            product_id: ID del producto
            quantity: cantidad
            extras: dict con extras {'leche': True, 'azucar': False}
        """
        if extras is None:
            extras = {}

        self._items.append({
            'product_id': product_id,
            'quantity': quantity,
            'extras': extras
        })
        return self

    def add_special_instructions(self, instructions):
        """Agregar instrucciones especiales"""
        self._special_instructions = instructions
        return self

    def build(self):
        """
        Construir la orden final

        Returns:
            Order creada y guardada
        """
        if not self._customer:
            raise ValueError("Cliente requerido para crear orden")

        if not self._items:
            raise ValueError("La orden debe tener al menos un item")

        # Crear orden
        order = Order.objects.create(
            customer=self._customer,
            mesero=self._mesero,
            table_number=self._table_number,
            special_instructions=self._special_instructions
        )

        # Agregar items
        for item_data in self._items:
            product = Product.objects.get(id=item_data['product_id'])

            item = OrderItem(
                order=order,
                product=product,
                quantity=item_data['quantity'],
                extras=item_data['extras']
            )
            item.calculate_subtotal()
            item.save()

        # Calcular total
        order.calculate_total()

        return order

    def reset(self):
        """Resetear el builder para construir otra orden"""
        self._customer = None
        self._mesero = None
        self._table_number = 1
        self._items = []
        self._special_instructions = ""
        return self


class OrderDirector:
    """
    Director que conoce secuencias específicas de construcción
    """

    def __init__(self, builder: OrderBuilder):
        self._builder = builder

    def build_simple_order(self, customer, table, product_id):
        """Construir orden simple con un producto"""
        return (self._builder
                .set_customer(customer)
                .set_table(table)
                .add_product(product_id)
                .build())

    def build_breakfast_order(self, customer, table, mesero, beverage_id, food_id):
        """Construir orden típica de desayuno"""
        return (self._builder
                .set_customer(customer)
                .set_table(table)
                .set_mesero(mesero)
                .add_product(beverage_id, extras={'leche': True})
                .add_product(food_id)
                .add_special_instructions("Desayuno")
                .build())

    def build_takeaway_order(self, customer, *product_ids):
        """Construir orden para llevar"""
        self._builder.set_customer(customer).set_table(0)

        for pid in product_ids:
            self._builder.add_product(pid)

        return (self._builder
                .add_special_instructions("PARA LLEVAR")
                .build())