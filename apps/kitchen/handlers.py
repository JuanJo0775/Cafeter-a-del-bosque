"""
CHAIN OF RESPONSIBILITY: Enrutamiento inteligente a estaciones de cocina
Cada handler decide si procesa el item o lo pasa al siguiente
"""
from abc import ABC, abstractmethod
from .models import KitchenStation, StationQueue
from datetime import datetime


class StationHandler(ABC):
    """
    Handler abstracto para estaciones de cocina
    Implementa cadena de responsabilidad
    """

    def __init__(self):
        self._next_handler = None
        self._station = None

    def set_next(self, handler):
        """
        Establecer siguiente handler en la cadena

        Args:
            handler: siguiente StationHandler

        Returns:
            handler (para encadenamiento fluido)
        """
        self._next_handler = handler
        return handler

    @abstractmethod
    def can_handle(self, order_item):
        """
        Determinar si este handler puede procesar el item

        Args:
            order_item: instancia de OrderItem

        Returns:
            bool
        """
        pass

    @abstractmethod
    def get_station_type(self):
        """Retornar tipo de estación que maneja"""
        pass

    def handle(self, order, order_item):
        """
        Intentar manejar el item, si no puede, pasar al siguiente

        Args:
            order: instancia de Order
            order_item: instancia de OrderItem

        Returns:
            KitchenStation asignada o None
        """
        if self.can_handle(order_item):
            return self.process(order, order_item)
        elif self._next_handler:
            print(f"[CHAIN] {self.get_station_type()} no puede manejar '{order_item.product.name}' → pasando al siguiente")
            return self._next_handler.handle(order, order_item)
        else:
            print(f"[CHAIN] ✗ Ninguna estación puede manejar '{order_item.product.name}'")
            return None

    def process(self, order, order_item):
        """
        Procesar el item en esta estación

        Args:
            order: instancia de Order
            order_item: instancia de OrderItem

        Returns:
            KitchenStation asignada
        """
        try:
            if not self._station:
                self._station = KitchenStation.objects.get(
                    station_type=self.get_station_type(),
                    is_active=True
                )

            # Verificar si ya existe en la cola
            existing = StationQueue.objects.filter(
                station=self._station,
                order=order,
                is_completed=False
            ).first()

            if not existing:
                queue_item = StationQueue.objects.create(
                    station=self._station,
                    order=order
                )

                print(f"[CHAIN] ✓ '{order_item.product.name}' → {self._station.name}")
                return self._station
            else:
                print(f"[CHAIN] ℹ Orden #{order.id} ya en cola de {self._station.name}")
                return self._station

        except KitchenStation.DoesNotExist:
            print(f"[CHAIN] ✗ Estación {self.get_station_type()} no encontrada")
            return None

    def get_priority(self, order_item):
        """
        Calcular prioridad del item (para ordenamiento)

        Returns:
            int (mayor = más prioritario)
        """
        priority = 0

        # Items con mayor tiempo de preparación tienen más prioridad
        priority += order_item.product.preparation_time

        # Bebidas calientes tienen prioridad
        if 'caliente' in order_item.product.name.lower():
            priority += 10

        return priority


class HotBeveragesHandler(StationHandler):
    """Handler para bebidas calientes (café, chocolate, té)"""

    def can_handle(self, order_item):
        """Verificar si es bebida caliente"""
        category = order_item.product.category
        product_name = order_item.product.name.lower()

        # Verificar categoría
        is_beverage = category.category_type == 'BEBIDAS'

        # Verificar si es caliente
        hot_keywords = ['caliente', 'café', 'cappuccino', 'latte', 'espresso',
                       'chocolate', 'té', 'infusion']

        is_hot = any(keyword in product_name for keyword in hot_keywords)

        return is_beverage and is_hot

    def get_station_type(self):
        return 'BEBIDAS_CALIENTES'

    def get_priority(self, order_item):
        """Bebidas calientes tienen alta prioridad"""
        base_priority = super().get_priority(order_item)
        return base_priority + 15


class ColdBeveragesHandler(StationHandler):
    """Handler para bebidas frías (jugos, batidos, refrescos)"""

    def can_handle(self, order_item):
        """Verificar si es bebida fría"""
        category = order_item.product.category
        product_name = order_item.product.name.lower()

        # Verificar categoría
        is_beverage = category.category_type == 'BEBIDAS'

        # Verificar si es fría
        cold_keywords = ['frí', 'frío', 'jugo', 'batido', 'smoothie',
                        'limonada', 'helado', 'frozen']

        is_cold = any(keyword in product_name for keyword in cold_keywords)

        return is_beverage and is_cold

    def get_station_type(self):
        return 'BEBIDAS_FRIAS'

    def get_priority(self, order_item):
        """Bebidas frías tienen prioridad media"""
        base_priority = super().get_priority(order_item)
        return base_priority + 10


class BakeryHandler(StationHandler):
    """Handler para panadería (panes, croissants, tostadas)"""

    def can_handle(self, order_item):
        """Verificar si es producto de panadería"""
        category = order_item.product.category
        product_name = order_item.product.name.lower()

        # Verificar categoría
        is_entry = category.category_type == 'ENTRADAS'

        # Verificar keywords de panadería
        bakery_keywords = ['pan', 'croissant', 'tostada', 'bagel',
                          'muffin', 'galleta', 'pretzel']

        is_bakery = any(keyword in product_name for keyword in bakery_keywords)

        return is_entry and is_bakery

    def get_station_type(self):
        return 'PANADERIA'

    def get_priority(self, order_item):
        """Panadería tiene prioridad media-alta"""
        base_priority = super().get_priority(order_item)
        return base_priority + 12


class MainKitchenHandler(StationHandler):
    """Handler para cocina principal (platos fuertes, comidas)"""

    def can_handle(self, order_item):
        """Verificar si es comida principal"""
        category = order_item.product.category
        product_name = order_item.product.name.lower()

        # Cualquier cosa en categoría COMIDAS
        is_main = category.category_type == 'COMIDAS'

        # Keywords adicionales
        food_keywords = ['sandwich', 'ensalada', 'hamburguesa', 'pizza',
                        'pasta', 'sopa', 'plato', 'bowl']

        has_food_keyword = any(keyword in product_name for keyword in food_keywords)

        return is_main or has_food_keyword

    def get_station_type(self):
        return 'COCINA'

    def get_priority(self, order_item):
        """Platos principales tienen alta prioridad"""
        base_priority = super().get_priority(order_item)
        return base_priority + 20


class DessertHandler(StationHandler):
    """Handler para postres (pasteles, helados, dulces)"""

    def can_handle(self, order_item):
        """Verificar si es postre"""
        category = order_item.product.category
        product_name = order_item.product.name.lower()

        # Verificar categoría
        is_dessert = category.category_type == 'POSTRES'

        # Keywords de postres
        dessert_keywords = ['pastel', 'torta', 'helado', 'brownie',
                          'cheesecake', 'flan', 'mousse', 'postre']

        has_dessert_keyword = any(keyword in product_name for keyword in dessert_keywords)

        return is_dessert or has_dessert_keyword

    def get_station_type(self):
        return 'POSTRES'

    def get_priority(self, order_item):
        """Postres tienen menor prioridad (se sirven al final)"""
        base_priority = super().get_priority(order_item)
        return base_priority + 5


class DefaultHandler(StationHandler):
    """Handler por defecto para items no clasificados"""

    def can_handle(self, order_item):
        """Acepta cualquier item"""
        return True

    def get_station_type(self):
        return 'COCINA'  # Enviar a cocina principal por defecto

    def process(self, order, order_item):
        """Procesar con advertencia"""
        print(f"[CHAIN] ⚠ '{order_item.product.name}' no clasificado → enviando a cocina principal")
        return super().process(order, order_item)


class KitchenRouter:
    """
    Router que construye y gestiona la cadena de handlers
    Punto de entrada para enrutamiento de órdenes
    """

    def __init__(self):
        self._build_chain()

    def _build_chain(self):
        """Construir cadena de responsabilidad"""
        print("[ROUTER] Construyendo cadena de handlers...")

        # Crear handlers
        self.hot_beverages = HotBeveragesHandler()
        self.cold_beverages = ColdBeveragesHandler()
        self.bakery = BakeryHandler()
        self.main_kitchen = MainKitchenHandler()
        self.dessert = DessertHandler()
        self.default = DefaultHandler()

        # Encadenar (orden de prioridad)
        self.hot_beverages.set_next(self.cold_beverages).set_next(
            self.bakery).set_next(self.main_kitchen).set_next(
            self.dessert).set_next(self.default)

        print("[ROUTER] ✓ Cadena construida: Bebidas Calientes → Bebidas Frías → Panadería → Cocina → Postres → Default")

    def route_order(self, order):
        """
        Enrutar todos los items de una orden a sus estaciones

        Args:
            order: instancia de Order

        Returns:
            dict con asignaciones por estación
        """
        print(f"\n[ROUTER] === Enrutando Orden #{order.id} ===")

        assignments = {}
        items_by_priority = []

        # Procesar cada item y calcular prioridad
        for item in order.items.all():
            # Obtener handler apropiado
            handler = self._get_handler_for_item(item)
            priority = handler.get_priority(item) if handler else 0

            items_by_priority.append((priority, item))

        # Ordenar por prioridad (mayor primero)
        items_by_priority.sort(reverse=True, key=lambda x: x[0])

        # Enrutar en orden de prioridad
        for priority, item in items_by_priority:
            station = self.hot_beverages.handle(order, item)

            if station:
                if station.name not in assignments:
                    assignments[station.name] = {
                        'station_type': station.station_type,
                        'items': []
                    }

                assignments[station.name]['items'].append({
                    'product': item.product.name,
                    'quantity': item.quantity,
                    'priority': priority,
                    'preparation_time': item.product.preparation_time
                })

        print(f"[ROUTER] ✓ Orden #{order.id} enrutada a {len(assignments)} estación(es)")
        print("[ROUTER] === Enrutamiento completado ===\n")

        return assignments

    def _get_handler_for_item(self, item):
        """Obtener handler apropiado para un item"""
        handlers = [
            self.hot_beverages,
            self.cold_beverages,
            self.bakery,
            self.main_kitchen,
            self.dessert
        ]

        for handler in handlers:
            if handler.can_handle(item):
                return handler

        return self.default

    def route_single_item(self, order, order_item):
        """
        Enrutar un item individual

        Args:
            order: instancia de Order
            order_item: instancia de OrderItem

        Returns:
            KitchenStation asignada
        """
        print(f"[ROUTER] Enrutando item individual: {order_item.product.name}")
        station = self.hot_beverages.handle(order, order_item)

        if station:
            print(f"[ROUTER] ✓ Item enrutado a {station.name}")
        else:
            print(f"[ROUTER] ✗ No se pudo enrutar item")

        return station

    def get_station_status(self):
        """
        Obtener estado de todas las estaciones

        Returns:
            lista con info de cada estación
        """
        stations = KitchenStation.objects.all()

        status = []
        for station in stations:
            pending = station.queue.filter(is_completed=False).count()
            completed_today = station.queue.filter(
                is_completed=True,
                completed_at__date=datetime.now().date()
            ).count()

            # Calcular tiempo promedio
            completed_items = station.queue.filter(
                is_completed=True,
                completed_at__isnull=False
            )

            avg_time = None
            if completed_items.exists():
                total_seconds = sum(
                    (item.completed_at - item.assigned_at).total_seconds()
                    for item in completed_items
                )
                avg_time = int(total_seconds / completed_items.count() / 60)  # minutos

            status.append({
                'id': station.id,
                'name': station.name,
                'type': station.station_type,
                'is_active': station.is_active,
                'pending_orders': pending,
                'completed_today': completed_today,
                'avg_preparation_time_minutes': avg_time,
                'capacity_status': 'high' if pending < 3 else 'medium' if pending < 6 else 'low'
            })

        return status

    def get_station_queue(self, station_type):
        """
        Obtener cola de una estación específica

        Args:
            station_type: tipo de estación

        Returns:
            QuerySet de StationQueue
        """
        try:
            station = KitchenStation.objects.get(station_type=station_type)
            return station.queue.filter(is_completed=False).order_by('assigned_at')
        except KitchenStation.DoesNotExist:
            return StationQueue.objects.none()

    def complete_station_item(self, station_type, order_id):
        """
        Marcar item como completado en una estación

        Args:
            station_type: tipo de estación
            order_id: ID de la orden

        Returns:
            bool éxito
        """
        try:
            station = KitchenStation.objects.get(station_type=station_type)
            queue_item = StationQueue.objects.get(
                station=station,
                order_id=order_id,
                is_completed=False
            )

            queue_item.is_completed = True
            queue_item.completed_at = datetime.now()
            queue_item.save()

            print(f"[ROUTER] ✓ Orden #{order_id} completada en {station.name}")

            # Verificar si todas las estaciones completaron la orden
            self._check_order_completion(order_id)

            return True

        except (KitchenStation.DoesNotExist, StationQueue.DoesNotExist):
            print(f"[ROUTER] ✗ No se encontró item en cola")
            return False

    def _check_order_completion(self, order_id):
        """Verificar si todas las estaciones completaron la orden"""
        from apps.orders.models import Order

        pending = StationQueue.objects.filter(
            order_id=order_id,
            is_completed=False
        ).count()

        if pending == 0:
            print(f"[ROUTER] 🎉 Todas las estaciones completaron orden #{order_id}")

            # Avanzar orden a LISTO automáticamente
            try:
                order = Order.objects.get(id=order_id)
                if order.status == 'EN_PREPARACION':
                    from apps.orders.patterns.state import OrderStateManager
                    OrderStateManager.advance_order(order)
            except Order.DoesNotExist:
                pass

    def get_chain_info(self):
        """Obtener información de la cadena"""
        return {
            'handlers': [
                {
                    'name': 'Bebidas Calientes',
                    'type': self.hot_beverages.get_station_type()
                },
                {
                    'name': 'Bebidas Frías',
                    'type': self.cold_beverages.get_station_type()
                },
                {
                    'name': 'Panadería',
                    'type': self.bakery.get_station_type()
                },
                {
                    'name': 'Cocina Principal',
                    'type': self.main_kitchen.get_station_type()
                },
                {
                    'name': 'Postres',
                    'type': self.dessert.get_station_type()
                }
            ],
            'total_handlers': 5
        }


def get_kitchen_router():
    """Helper para obtener router singleton"""
    return KitchenRouter()