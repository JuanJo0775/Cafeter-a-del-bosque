"""
STRATEGY: Estrategias de precios según temporada y contexto
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from datetime import time, datetime


class PricingStrategy(ABC):
    """Estrategia abstracta para cálculo de precios"""

    @abstractmethod
    def calculate_price(self, base_price):
        """Calcular precio según estrategia"""
        pass

    @abstractmethod
    def get_discount_percentage(self):
        """Obtener porcentaje de descuento/incremento"""
        pass

    @abstractmethod
    def get_strategy_name(self):
        """Nombre de la estrategia"""
        pass

    def applies_to_product(self, product):
        """Determinar si la estrategia aplica a este producto"""
        return True


class RegularPricingStrategy(PricingStrategy):
    """Precios regulares sin modificación"""

    def calculate_price(self, base_price):
        return Decimal(str(base_price))

    def get_discount_percentage(self):
        return 0

    def get_strategy_name(self):
        return "Regular"


class SeasonalPricingStrategy(PricingStrategy):
    """Estrategia base para precios por temporada"""

    def __init__(self, season, modifier=Decimal('1.0')):
        self.season = season
        self.modifier = modifier

    def calculate_price(self, base_price):
        return Decimal(str(base_price)) * self.modifier

    def get_discount_percentage(self):
        return int((self.modifier - Decimal('1.0')) * 100)

    def applies_to_product(self, product):
        """Solo aplica a productos de la temporada o sin temporada"""
        return product.season == self.season or product.season is None

    def get_strategy_name(self):
        return f"Seasonal - {self.season}"


class WinterPricingStrategy(SeasonalPricingStrategy):
    """Incremento del 10% en bebidas calientes en invierno"""

    def __init__(self):
        super().__init__('INVIERNO', Decimal('1.10'))

    def applies_to_product(self, product):
        is_seasonal_product = super().applies_to_product(product)
        is_hot_beverage = (
                product.category.category_type == 'BEBIDAS' and
                ('caliente' in product.name.lower() or 'café' in product.name.lower())
        )
        return is_seasonal_product and is_hot_beverage


class SummerPricingStrategy(SeasonalPricingStrategy):
    """Descuento del 15% en bebidas frías en verano"""

    def __init__(self):
        super().__init__('VERANO', Decimal('0.85'))

    def applies_to_product(self, product):
        is_seasonal_product = super().applies_to_product(product)
        is_cold_beverage = (
                product.category.category_type == 'BEBIDAS' and
                ('frí' in product.name.lower() or 'jugo' in product.name.lower() or 'batido' in product.name.lower())
        )
        return is_seasonal_product and is_cold_beverage


class HappyHourPricingStrategy(PricingStrategy):
    """20% descuento en bebidas durante happy hour (3pm - 6pm)"""

    def __init__(self):
        self.start_time = time(15, 0)  # 3:00 PM
        self.end_time = time(18, 0)  # 6:00 PM

    def calculate_price(self, base_price):
        if self.is_happy_hour():
            return Decimal(str(base_price)) * Decimal('0.80')
        return Decimal(str(base_price))

    def get_discount_percentage(self):
        return 20 if self.is_happy_hour() else 0

    def is_happy_hour(self):
        """Verificar si estamos en happy hour"""
        current_time = datetime.now().time()
        return self.start_time <= current_time <= self.end_time

    def applies_to_product(self, product):
        """Solo aplica a bebidas"""
        return product.category.category_type == 'BEBIDAS' and self.is_happy_hour()

    def get_strategy_name(self):
        return "Happy Hour"


class WeekendPricingStrategy(PricingStrategy):
    """5% incremento en fines de semana"""

    def calculate_price(self, base_price):
        if self.is_weekend():
            return Decimal(str(base_price)) * Decimal('1.05')
        return Decimal(str(base_price))

    def get_discount_percentage(self):
        return -5 if self.is_weekend() else 0

    def is_weekend(self):
        """Verificar si es fin de semana"""
        return datetime.now().weekday() >= 5  # Sábado=5, Domingo=6

    def get_strategy_name(self):
        return "Weekend"


class ComboDiscountStrategy(PricingStrategy):
    """10% descuento cuando se pide combo (bebida + comida)"""

    def __init__(self, has_combo=False):
        self.has_combo = has_combo

    def calculate_price(self, base_price):
        if self.has_combo:
            return Decimal(str(base_price)) * Decimal('0.90')
        return Decimal(str(base_price))

    def get_discount_percentage(self):
        return 10 if self.has_combo else 0

    def get_strategy_name(self):
        return "Combo Discount"


class LoyaltyPricingStrategy(PricingStrategy):
    """Descuentos por lealtad según historial del cliente"""

    def __init__(self, customer_tier='regular'):
        self.customer_tier = customer_tier
        self.discounts = {
            'regular': Decimal('1.00'),  # Sin descuento
            'bronze': Decimal('0.95'),  # 5% descuento
            'silver': Decimal('0.90'),  # 10% descuento
            'gold': Decimal('0.85'),  # 15% descuento
            'platinum': Decimal('0.80')  # 20% descuento
        }

    def calculate_price(self, base_price):
        multiplier = self.discounts.get(self.customer_tier, Decimal('1.00'))
        return Decimal(str(base_price)) * multiplier

    def get_discount_percentage(self):
        multiplier = self.discounts.get(self.customer_tier, Decimal('1.00'))
        return int((Decimal('1.0') - multiplier) * 100)

    def get_strategy_name(self):
        return f"Loyalty - {self.customer_tier.title()}"


class PricingContext:
    """
    Contexto que aplica la estrategia de precios apropiada
    """

    def __init__(self, strategy: PricingStrategy = None):
        self._strategy = strategy or RegularPricingStrategy()

    def set_strategy(self, strategy: PricingStrategy):
        """Cambiar estrategia"""
        self._strategy = strategy
        print(f"[STRATEGY] Estrategia de precios cambiada a: {strategy.get_strategy_name()}")

    def calculate_price(self, product):
        """
        Calcular precio con estrategia actual

        Args:
            product: instancia de Product

        Returns:
            Decimal con precio calculado
        """
        if not self._strategy.applies_to_product(product):
            return product.base_price

        return self._strategy.calculate_price(product.base_price)

    def get_price_info(self, product):
        """
        Obtener información completa de precio

        Returns:
            dict con detalles
        """
        final_price = self.calculate_price(product)
        discount = self._strategy.get_discount_percentage()

        return {
            'product_id': product.id,
            'product_name': product.name,
            'base_price': float(product.base_price),
            'final_price': float(final_price),
            'discount_percentage': discount,
            'strategy': self._strategy.get_strategy_name(),
            'savings': float(product.base_price - final_price)
        }


def get_pricing_strategy_for_season(season):
    """
    Obtener estrategia apropiada según temporada

    Args:
        season: 'REGULAR', 'INVIERNO', 'VERANO', etc.

    Returns:
        PricingStrategy
    """
    strategies = {
        'INVIERNO': WinterPricingStrategy(),
        'VERANO': SummerPricingStrategy(),
        'REGULAR': RegularPricingStrategy()
    }

    return strategies.get(season, RegularPricingStrategy())