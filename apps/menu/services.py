"""
Servicios de menú - Patrones ABSTRACT FACTORY y STRATEGY
"""
from abc import ABC, abstractmethod
from decimal import Decimal


# ==================== ABSTRACT FACTORY ====================

class MenuFactory(ABC):
    """
    Abstract Factory para crear familias de menús
    según temporada o contexto
    """

    @abstractmethod
    def create_breakfast_menu(self):
        """Crear menú de desayuno"""
        pass

    @abstractmethod
    def create_lunch_menu(self):
        """Crear menú de almuerzo"""
        pass

    @abstractmethod
    def create_dinner_menu(self):
        """Crear menú de cena"""
        pass

    @abstractmethod
    def get_pricing_strategy(self):
        """Obtener estrategia de precios"""
        pass


class RegularMenuFactory(MenuFactory):
    """Factory para menú regular"""

    def create_breakfast_menu(self):
        from .models import Category
        return Category.objects.filter(
            category_type__in=['BEBIDAS', 'ENTRADAS']
        ).prefetch_related('products')

    def create_lunch_menu(self):
        from .models import Category
        return Category.objects.filter(
            category_type__in=['COMIDAS', 'BEBIDAS']
        ).prefetch_related('products')

    def create_dinner_menu(self):
        from .models import Category
        return Category.objects.filter(
            category_type__in=['COMIDAS', 'POSTRES', 'BEBIDAS']
        ).prefetch_related('products')

    def get_pricing_strategy(self):
        return RegularPricingStrategy()


class HolidayMenuFactory(MenuFactory):
    """Factory para menú de temporada navideña"""

    def create_breakfast_menu(self):
        from .models import Category
        # Menú especial con bebidas calientes navideñas
        return Category.objects.filter(
            category_type='BEBIDAS'
        ).prefetch_related('products')

    def create_lunch_menu(self):
        from .models import Category
        return Category.objects.filter(
            category_type__in=['COMIDAS', 'POSTRES']
        ).prefetch_related('products')

    def create_dinner_menu(self):
        from .models import Category
        return Category.objects.all().prefetch_related('products')

    def get_pricing_strategy(self):
        return HolidayPricingStrategy()


class SummerMenuFactory(MenuFactory):
    """Factory para menú de verano"""

    def create_breakfast_menu(self):
        from .models import Category
        return Category.objects.filter(
            category_type__in=['BEBIDAS', 'ENTRADAS']
        ).prefetch_related('products')

    def create_lunch_menu(self):
        from .models import Category
        # Énfasis en bebidas frías
        return Category.objects.filter(
            category_type='BEBIDAS'
        ).prefetch_related('products')

    def create_dinner_menu(self):
        from .models import Category
        return Category.objects.filter(
            category_type__in=['COMIDAS', 'BEBIDAS']
        ).prefetch_related('products')

    def get_pricing_strategy(self):
        return SummerPricingStrategy()


# ==================== STRATEGY ====================

class PricingStrategy(ABC):
    """
    Estrategia abstracta para cálculo de precios
    """

    @abstractmethod
    def calculate_price(self, base_price):
        """Calcular precio según estrategia"""
        pass

    @abstractmethod
    def get_discount_percentage(self):
        """Obtener porcentaje de descuento"""
        pass


class RegularPricingStrategy(PricingStrategy):
    """Estrategia de precios regulares"""

    def calculate_price(self, base_price):
        return Decimal(str(base_price))

    def get_discount_percentage(self):
        return 0


class HolidayPricingStrategy(PricingStrategy):
    """Estrategia de precios para temporada alta (10% incremento)"""

    def calculate_price(self, base_price):
        return Decimal(str(base_price)) * Decimal('1.10')

    def get_discount_percentage(self):
        return -10  # Incremento


class SummerPricingStrategy(PricingStrategy):
    """Estrategia de precios de verano (15% descuento en bebidas frías)"""

    def calculate_price(self, base_price):
        return Decimal(str(base_price)) * Decimal('0.85')

    def get_discount_percentage(self):
        return 15


class HappyHourPricingStrategy(PricingStrategy):
    """Estrategia de happy hour (20% descuento)"""

    def calculate_price(self, base_price):
        return Decimal(str(base_price)) * Decimal('0.80')

    def get_discount_percentage(self):
        return 20


# ==================== SERVICE ====================

class MenuService:
    """Servicio para gestión de menús"""

    def __init__(self, factory: MenuFactory = None):
        self.factory = factory or RegularMenuFactory()

    def get_menu_by_time(self, time_of_day):
        """
        Obtener menú según hora del día

        Args:
            time_of_day: 'breakfast', 'lunch', 'dinner'
        """
        if time_of_day == 'breakfast':
            return self.factory.create_breakfast_menu()
        elif time_of_day == 'lunch':
            return self.factory.create_lunch_menu()
        elif time_of_day == 'dinner':
            return self.factory.create_dinner_menu()
        else:
            return self.factory.create_lunch_menu()

    def apply_pricing(self, products):
        """Aplicar estrategia de precios a productos"""
        strategy = self.factory.get_pricing_strategy()

        result = []
        for product in products:
            result.append({
                'id': product.id,
                'name': product.name,
                'base_price': float(product.base_price),
                'final_price': float(strategy.calculate_price(product.base_price)),
                'discount': strategy.get_discount_percentage()
            })

        return result


def get_menu_factory(season='regular'):
    """
    Obtener factory según temporada

    Args:
        season: 'regular', 'holiday', 'summer'
    """
    factories = {
        'regular': RegularMenuFactory(),
        'holiday': HolidayMenuFactory(),
        'summer': SummerMenuFactory(),
    }
    return factories.get(season, RegularMenuFactory())