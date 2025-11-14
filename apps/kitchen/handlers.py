"""
Patrón CHAIN OF RESPONSIBILITY para enrutar órdenes a estaciones de cocina
"""
from abc import ABC, abstractmethod
from .models import KitchenStation, StationQueue


class StationHandler(ABC):
    """
    Handler abstracto para estaciones de cocina
    Parte de la cadena de responsabilidad
    """

    def __init__(self):
        self._next_handler = None

    def set_next(self, handler):
        """Establecer siguiente handler en la cadena"""
        self._next_handler = handler
        return handler

    @abstractmethod
    def can_handle(self, order_item):
        """¿Puede esta estación manejar el item?"""
        pass

    def handle(self, order, order_item):
        """
        Intentar manejar el item, si no puede, pasar al siguiente
        """
        if self.can_handle(order_item):
            return self.process(order, order_item)
        elif self._next_handler:
            return self._next_handler.handle(order, order_item)
        else:
            return None

    @abstractmethod
    def process(self, order, order_item):
        """Procesar el item en esta estación"""
        pass


class HotBeveragesHandler(StationHandler):
    """Handler para bebidas calientes"""

    def can_handle(self, order_item):
        """Verificar si es bebida caliente"""
        category_type = order_item.product.category.category_type
        product_name = order_item.product.name.lower()

        is_hot = 'caliente' in product_name or 'café' in product_name or 'chocolate' in product_name

        return category_type == 'BEBIDAS' and is_hot

    def process(self, order, order_item):
        """Asignar a estación de bebidas calientes"""
        try:
            station = KitchenStation.objects.get(station_type='BEBIDAS_CALIENTES')

            queue_item = StationQueue.objects.create(
                station=station,
                order=order
            )

            print(f"[CHAIN] Orden #{order.id} → {station.name} (Bebida Caliente: {order_item.product.name})")
            return station
        except KitchenStation.DoesNotExist:
            print(f"[CHAIN] Estación de bebidas calientes no encontrada")
            return None


class ColdBeveragesHandler(StationHandler):
    """Handler para bebidas frías"""

    def can_handle(self, order_item):
        """Verificar si es bebida fría"""
        category_type = order_item.product.category.category_type
        product_name = order_item.product.name.lower()

        is_cold = 'frí' in product_name or 'jugo' in product_name or 'batido' in product_name

        return category_type == 'BEBIDAS' and is_cold

    def process(self, order, order_item):
        """Asignar a estación de bebidas frías"""
        try:
            station = KitchenStation.objects.get(station_type='BEBIDAS_FRIAS')

            StationQueue.objects.create(
                station=station,
                order=order
            )

            print(f"[CHAIN] Orden #{order.id} → {station.name} (Bebida Fría: {order_item.product.name})")
            return station
        except KitchenStation.DoesNotExist:
            return None


class BakeryHandler(StationHandler):
    """Handler para panadería"""

    def can_handle(self, order_item):
        """Verificar si es producto de panadería"""
        return order_item.product.category.category_type == 'ENTRADAS'

    def process(self, order, order_item):
        """Asignar a panadería"""
        try:
            station = KitchenStation.objects.get(station_type='PANADERIA')

            StationQueue.objects.create(
                station=station,
                order=order
            )

            print(f"[CHAIN] Orden #{order.id} → {station.name} (Panadería: {order_item.product.name})")
            return station
        except KitchenStation.DoesNotExist:
            return None


class MainKitchenHandler(StationHandler):
    """Handler para cocina principal (comidas)"""

    def can_handle(self, order_item):
        """Verificar si es comida principal"""
        return order_item.product.category.category_type == 'COMIDAS'

    def process(self, order, order_item):
        """Asignar a cocina principal"""
        try:
            station = KitchenStation.objects.get(station_type='COCINA')

            StationQueue.objects.create(
                station=station,
                order=order
            )

            print(f"[CHAIN] Orden #{order.id} → {station.name} (Comida: {order_item.product.name})")
            return station
        except KitchenStation.DoesNotExist:
            return None


class DessertHandler(StationHandler):
    """Handler para postres"""

    def can_handle(self, order_item):
        """Verificar si es postre"""
        return order_item.product.category.category_type == 'POSTRES'

    def process(self, order, order_item):
        """Asignar a repostería"""
        try:
            station = KitchenStation.objects.get(station_type='POSTRES')

            StationQueue.objects.create(
                station=station,
                order=order
            )

            print(f"[CHAIN] Orden #{order.id} → {station.name} (Postre: {order_item.product.name})")
            return station
        except KitchenStation.DoesNotExist:
            return None


class KitchenRouter:
    """
    Router que construye la cadena y enruta órdenes
    """

    def __init__(self):
        # Construir cadena de responsabilidad
        self.hot_beverages = HotBeveragesHandler()
        self.cold_beverages = ColdBeveragesHandler()
        self.bakery = BakeryHandler()
        self.main_kitchen = MainKitchenHandler()
        self.dessert = DessertHandler()

        # Encadenar
        self.hot_beverages.set_next(self.cold_beverages).set_next(
            self.bakery).set_next(self.main_kitchen).set_next(self.dessert)

    def route_order(self, order):
        """
        Enrutar todos los items de una orden a sus estaciones

        Args:
            order: instancia de Order

        Returns:
            dict con asignaciones
        """
        assignments = {}

        for item in order.items.all():
            station = self.hot_beverages.handle(order, item)

            if station:
                if station.name not in assignments:
                    assignments[station.name] = []
                assignments[station.name].append(item.product.name)

        return assignments

    def get_station_status(self):
        """Obtener estado de todas las estaciones"""
        stations = KitchenStation.objects.all()

        status = []
        for station in stations:
            pending = station.queue.filter(is_completed=False).count()

            status.append({
                'name': station.name,
                'type': station.station_type,
                'is_active': station.is_active,
                'pending_orders': pending
            })

        return status