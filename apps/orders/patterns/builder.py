"""
BUILDER: Construir órdenes paso a paso con validaciones y flujo completo
"""
from apps.orders.models import Order, OrderItem
from apps.menu.models import Product
from apps.menu.decorators.product_decorator import DecoratorFactory
from decimal import Decimal


class OrderBuilder:
    """
    Builder mejorado para construir órdenes complejas paso a paso
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """Resetear builder para nueva orden"""
        self._customer = None
        self._mesero = None
        self._table_number = None
        self._items = []
        self._special_instructions = ""
        self._validated = False
        print("[BUILDER] Builder reseteado")

    def set_customer(self, customer):
        """
        Establecer cliente

        Args:
            customer: instancia de User con role='CLIENTE'
        """
        if customer.role != 'CLIENTE':
            raise ValueError(f"Usuario debe ser CLIENTE, no {customer.role}")

        self._customer = customer
        print(f"[BUILDER] Cliente establecido: {customer.username}")
        return self

    def set_mesero(self, mesero):
        """
        Establecer mesero (opcional)

        Args:
            mesero: instancia de User con role='MESERO'
        """
        if mesero and mesero.role != 'MESERO':
            raise ValueError(f"Usuario debe ser MESERO, no {mesero.role}")

        self._mesero = mesero
        print(f"[BUILDER] Mesero asignado: {mesero.username if mesero else 'Sin asignar'}")
        return self

    def set_table(self, table_number):
        """
        Establecer número de mesa

        Args:
            table_number: int (0 para para llevar)
        """
        if not isinstance(table_number, int) or table_number < 0:
            raise ValueError("Número de mesa debe ser entero >= 0")

        self._table_number = table_number

        if table_number == 0:
            print("[BUILDER] Mesa establecida: PARA LLEVAR")
        else:
            print(f"[BUILDER] Mesa establecida: {table_number}")

        return self

    def add_product(self, product_id, quantity=1, extras=None):
        """
        Agregar producto con extras

        Args:
            product_id: ID del producto
            quantity: cantidad (default 1)
            extras: dict con extras personalizados
        """
        if quantity <= 0:
            raise ValueError("Cantidad debe ser mayor a 0")

        try:
            product = Product.objects.get(id=product_id, is_available=True)
        except Product.DoesNotExist:
            raise ValueError(f"Producto {product_id} no disponible")

        if extras is None:
            extras = {}

        # Calcular precio con decoradores
        decorated_info = DecoratorFactory.get_decorated_info(product, extras)

        item_data = {
            'product': product,
            'product_id': product_id,
            'quantity': quantity,
            'extras': extras,
            'unit_price': Decimal(str(decorated_info['price'])),
            'subtotal': Decimal(str(decorated_info['price'])) * quantity,
            'decorated_name': decorated_info['name']
        }

        self._items.append(item_data)

        print(f"[BUILDER] Producto agregado: {decorated_info['name']} x{quantity} = ${item_data['subtotal']}")
        return self

    def add_multiple_products(self, products_list):
        """
        Agregar múltiples productos de una vez

        Args:
            products_list: lista de dicts [{'product_id': 1, 'quantity': 2, 'extras': {...}}]
        """
        for item in products_list:
            self.add_product(
                product_id=item['product_id'],
                quantity=item.get('quantity', 1),
                extras=item.get('extras', {})
            )

        return self

    def remove_product(self, product_id):
        """Remover producto de la orden"""
        original_length = len(self._items)
        self._items = [item for item in self._items if item['product_id'] != product_id]

        removed = original_length - len(self._items)
        if removed > 0:
            print(f"[BUILDER] Producto {product_id} removido ({removed} items)")

        return self

    def update_quantity(self, product_id, new_quantity):
        """Actualizar cantidad de un producto"""
        if new_quantity <= 0:
            return self.remove_product(product_id)

        for item in self._items:
            if item['product_id'] == product_id:
                item['quantity'] = new_quantity
                item['subtotal'] = item['unit_price'] * new_quantity
                print(f"[BUILDER] Cantidad actualizada: {item['decorated_name']} -> {new_quantity}")

        return self

    def add_special_instructions(self, instructions):
        """
        Agregar instrucciones especiales

        Args:
            instructions: str con instrucciones
        """
        self._special_instructions = instructions
        print(f"[BUILDER] Instrucciones especiales: {instructions}")
        return self

    def clear_special_instructions(self):
        """Limpiar instrucciones especiales"""
        self._special_instructions = ""
        print("[BUILDER] Instrucciones especiales limpiadas")
        return self

    def validate(self):
        """
        Validar que la orden está completa y correcta

        Returns:
            bool, lista de errores
        """
        errors = []

        if not self._customer:
            errors.append("Cliente requerido")

        if self._table_number is None:
            errors.append("Número de mesa requerido")

        if not self._items:
            errors.append("La orden debe tener al menos un producto")

        # Validar disponibilidad de productos
        for item in self._items:
            product = item['product']
            if not product.is_available:
                errors.append(f"Producto '{product.name}' no está disponible")

        self._validated = len(errors) == 0

        if self._validated:
            print("[BUILDER] ✓ Validación exitosa")
        else:
            print(f"[BUILDER] ✗ Errores de validación: {errors}")

        return self._validated, errors

    def get_total(self):
        """Calcular total de la orden"""
        total = sum(item['subtotal'] for item in self._items)
        return total

    def get_summary(self):
        """
        Obtener resumen de la orden antes de construir

        Returns:
            dict con resumen
        """
        return {
            'customer': self._customer.username if self._customer else None,
            'mesero': self._mesero.username if self._mesero else None,
            'table': self._table_number,
            'items_count': len(self._items),
            'items': [
                {
                    'name': item['decorated_name'],
                    'quantity': item['quantity'],
                    'unit_price': float(item['unit_price']),
                    'subtotal': float(item['subtotal'])
                }
                for item in self._items
            ],
            'special_instructions': self._special_instructions,
            'total': float(self.get_total()),
            'validated': self._validated
        }

    def build(self):
        """
        Construir y guardar la orden final

        Returns:
            Order guardada en BD
        """
        # Validar antes de construir
        is_valid, errors = self.validate()

        if not is_valid:
            raise ValueError(f"Orden inválida: {', '.join(errors)}")

        print("[BUILDER] Construyendo orden...")

        # Crear orden
        order = Order.objects.create(
            customer=self._customer,
            mesero=self._mesero,
            table_number=self._table_number,
            special_instructions=self._special_instructions,
            status='PENDIENTE'
        )

        print(f"[BUILDER] Orden #{order.id} creada - Estado: {order.status}")

        # Agregar items
        for item_data in self._items:
            order_item = OrderItem.objects.create(
                order=order,
                product=item_data['product'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                extras=item_data['extras']
            )
            order_item.calculate_subtotal()

            print(f"[BUILDER] Item agregado: {item_data['decorated_name']} x{item_data['quantity']}")

        # Calcular total
        order.calculate_total()

        print(f"[BUILDER] ✓ Orden #{order.id} construida - Total: ${order.total_price}")

        return order


class OrderDirector:
    """
    Director que conoce secuencias específicas de construcción
    Plantillas pre-definidas para tipos comunes de órdenes
    """

    def __init__(self):
        self.builder = OrderBuilder()

    def build_simple_coffee_order(self, customer, table, coffee_id):
        """
        Orden simple: un café

        Args:
            customer: User
            table: int
            coffee_id: ID del café

        Returns:
            Order
        """
        print("[DIRECTOR] Construyendo orden simple de café...")

        return (self.builder
                .reset()
                .set_customer(customer)
                .set_table(table)
                .add_product(coffee_id, quantity=1)
                .build())

    def build_breakfast_combo(self, customer, table, mesero, beverage_id, food_id):
        """
        Combo de desayuno: bebida + comida

        Args:
            customer: User
            table: int
            mesero: User
            beverage_id: ID de bebida
            food_id: ID de comida

        Returns:
            Order
        """
        print("[DIRECTOR] Construyendo combo de desayuno...")

        return (self.builder
                .reset()
                .set_customer(customer)
                .set_table(table)
                .set_mesero(mesero)
                .add_product(beverage_id, quantity=1, extras={'leche': True})
                .add_product(food_id, quantity=1)
                .add_special_instructions("Combo desayuno")
                .build())

    def build_takeaway_order(self, customer, product_ids):
        """
        Orden para llevar

        Args:
            customer: User
            product_ids: lista de IDs de productos

        Returns:
            Order
        """
        print("[DIRECTOR] Construyendo orden para llevar...")

        self.builder.reset()
        self.builder.set_customer(customer)
        self.builder.set_table(0)  # 0 = para llevar

        for pid in product_ids:
            self.builder.add_product(pid, quantity=1)

        self.builder.add_special_instructions("PARA LLEVAR")

        return self.builder.build()

    def build_group_order(self, customer, table, mesero, items_list):
        """
        Orden para grupo (múltiples productos)

        Args:
            customer: User
            table: int
            mesero: User
            items_list: lista de dicts con productos

        Returns:
            Order
        """
        print("[DIRECTOR] Construyendo orden para grupo...")

        return (self.builder
                .reset()
                .set_customer(customer)
                .set_table(table)
                .set_mesero(mesero)
                .add_multiple_products(items_list)
                .add_special_instructions("Orden para grupo - servir todos juntos")
                .build())

    def build_custom_order(self, customer, table, items, mesero=None, instructions=""):
        """
        Orden personalizada completa

        Args:
            customer: User
            table: int
            items: lista de productos
            mesero: User (opcional)
            instructions: str (opcional)

        Returns:
            Order
        """
        print("[DIRECTOR] Construyendo orden personalizada...")

        self.builder.reset()
        self.builder.set_customer(customer)
        self.builder.set_table(table)

        if mesero:
            self.builder.set_mesero(mesero)

        self.builder.add_multiple_products(items)

        if instructions:
            self.builder.add_special_instructions(instructions)

        return self.builder.build()