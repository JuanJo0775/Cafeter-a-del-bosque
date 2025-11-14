"""
DECORATOR: Añadir extras personalizados a productos dinámicamente
"""
from abc import ABC, abstractmethod
from decimal import Decimal


class ProductComponent(ABC):
    """Componente base para productos"""

    @abstractmethod
    def get_name(self):
        pass

    @abstractmethod
    def get_price(self):
        pass

    @abstractmethod
    def get_description(self):
        pass

    @abstractmethod
    def get_preparation_time(self):
        pass


class ConcreteProduct(ProductComponent):
    """Producto concreto (wrapper para Product model)"""

    def __init__(self, product):
        self._product = product

    def get_name(self):
        return self._product.name

    def get_price(self):
        return self._product.base_price

    def get_description(self):
        return self._product.description

    def get_preparation_time(self):
        return self._product.preparation_time

    def get_product(self):
        """Acceso al producto original"""
        return self._product


class ProductDecorator(ProductComponent):
    """Decorador base para productos"""

    def __init__(self, product_component: ProductComponent):
        self._component = product_component

    def get_name(self):
        return self._component.get_name()

    def get_price(self):
        return self._component.get_price()

    def get_description(self):
        return self._component.get_description()

    def get_preparation_time(self):
        return self._component.get_preparation_time()


class ExtraMilkDecorator(ProductDecorator):
    """Decorador: Agregar leche extra"""

    def __init__(self, product_component: ProductComponent, milk_type='regular'):
        super().__init__(product_component)
        self.milk_type = milk_type
        self.price_map = {
            'regular': Decimal('0.50'),
            'deslactosada': Decimal('0.80'),
            'almendra': Decimal('1.00'),
            'soya': Decimal('0.90')
        }

    def get_name(self):
        milk_names = {
            'regular': 'con leche',
            'deslactosada': 'con leche deslactosada',
            'almendra': 'con leche de almendra',
            'soya': 'con leche de soya'
        }
        return f"{self._component.get_name()} {milk_names.get(self.milk_type, 'con leche')}"

    def get_price(self):
        return self._component.get_price() + self.price_map.get(self.milk_type, Decimal('0.50'))

    def get_description(self):
        return f"{self._component.get_description()} (+ leche {self.milk_type})"


class ExtraShotDecorator(ProductDecorator):
    """Decorador: Shot extra de café"""

    def __init__(self, product_component: ProductComponent, shots=1):
        super().__init__(product_component)
        self.shots = shots

    def get_name(self):
        return f"{self._component.get_name()} + {self.shots} shot{'s' if self.shots > 1 else ''}"

    def get_price(self):
        return self._component.get_price() + (Decimal('1.00') * self.shots)

    def get_preparation_time(self):
        return self._component.get_preparation_time() + (1 * self.shots)


class ExtraCheeseDecorator(ProductDecorator):
    """Decorador: Queso extra"""

    def get_name(self):
        return f"{self._component.get_name()} + queso"

    def get_price(self):
        return self._component.get_price() + Decimal('0.50')


class ExtraAvocadoDecorator(ProductDecorator):
    """Decorador: Aguacate extra"""

    def get_name(self):
        return f"{self._component.get_name()} + aguacate"

    def get_price(self):
        return self._component.get_price() + Decimal('1.00')


class ExtraProteinDecorator(ProductDecorator):
    """Decorador: Proteína extra"""

    def __init__(self, product_component: ProductComponent, protein_type='pollo'):
        super().__init__(product_component)
        self.protein_type = protein_type
        self.price_map = {
            'pollo': Decimal('2.00'),
            'carne': Decimal('2.50'),
            'pescado': Decimal('3.00'),
            'tofu': Decimal('1.50')
        }

    def get_name(self):
        return f"{self._component.get_name()} + {self.protein_type}"

    def get_price(self):
        return self._component.get_price() + self.price_map.get(self.protein_type, Decimal('2.00'))

    def get_preparation_time(self):
        return self._component.get_preparation_time() + 3


class SizeDecorator(ProductDecorator):
    """Decorador: Cambiar tamaño"""

    def __init__(self, product_component: ProductComponent, size='regular'):
        super().__init__(product_component)
        self.size = size
        self.multipliers = {
            'pequeño': Decimal('0.80'),
            'regular': Decimal('1.00'),
            'grande': Decimal('1.30'),
            'extra_grande': Decimal('1.50')
        }

    def get_name(self):
        size_names = {
            'pequeño': 'Pequeño',
            'regular': 'Regular',
            'grande': 'Grande',
            'extra_grande': 'Extra Grande'
        }
        return f"{self._component.get_name()} ({size_names.get(self.size, 'Regular')})"

    def get_price(self):
        base_price = self._component.get_price()
        multiplier = self.multipliers.get(self.size, Decimal('1.00'))
        return base_price * multiplier


class IceLevelDecorator(ProductDecorator):
    """Decorador: Nivel de hielo para bebidas frías"""

    def __init__(self, product_component: ProductComponent, ice_level='normal'):
        super().__init__(product_component)
        self.ice_level = ice_level

    def get_name(self):
        ice_names = {
            'sin_hielo': 'sin hielo',
            'poco_hielo': 'con poco hielo',
            'normal': '',
            'extra_hielo': 'con extra hielo'
        }
        ice_text = ice_names.get(self.ice_level, '')
        base_name = self._component.get_name()
        return f"{base_name} {ice_text}".strip()


class SweetenerDecorator(ProductDecorator):
    """Decorador: Nivel de azúcar/edulcorante"""

    def __init__(self, product_component: ProductComponent, sweetener_type='azucar', level='normal'):
        super().__init__(product_component)
        self.sweetener_type = sweetener_type
        self.level = level

        # Precio extra solo para edulcorantes especiales
        self.extra_prices = {
            'stevia': Decimal('0.20'),
            'splenda': Decimal('0.20'),
            'miel': Decimal('0.30')
        }

    def get_name(self):
        if self.level == 'sin_azucar':
            return f"{self._component.get_name()} (sin azúcar)"
        elif self.sweetener_type != 'azucar':
            return f"{self._component.get_name()} (con {self.sweetener_type})"
        return self._component.get_name()

    def get_price(self):
        base_price = self._component.get_price()
        extra = self.extra_prices.get(self.sweetener_type, Decimal('0'))
        return base_price + extra


class ToppingDecorator(ProductDecorator):
    """Decorador: Toppings para postres"""

    def __init__(self, product_component: ProductComponent, toppings=None):
        super().__init__(product_component)
        self.toppings = toppings or []
        self.topping_prices = {
            'crema': Decimal('0.50'),
            'chocolate': Decimal('0.50'),
            'caramelo': Decimal('0.50'),
            'frutos_rojos': Decimal('0.80'),
            'nueces': Decimal('0.70'),
            'chispas': Decimal('0.40')
        }

    def get_name(self):
        if not self.toppings:
            return self._component.get_name()
        topping_str = ', '.join(self.toppings)
        return f"{self._component.get_name()} + {topping_str}"

    def get_price(self):
        base_price = self._component.get_price()
        extra = sum(self.topping_prices.get(t, Decimal('0.50')) for t in self.toppings)
        return base_price + extra


class DecoratorFactory:
    """Factory para crear decoradores según extras solicitados"""

    @staticmethod
    def apply_extras(product, extras_dict):
        """
        Aplicar extras a un producto

        Args:
            product: instancia de Product (modelo Django)
            extras_dict: dict con extras {'leche': 'deslactosada', 'shots': 2, ...}

        Returns:
            ProductComponent decorado con precio y descripción final
        """
        # Envolver producto en componente concreto
        component = ConcreteProduct(product)

        # Aplicar decoradores según extras
        if 'leche' in extras_dict and extras_dict['leche']:
            milk_type = extras_dict.get('leche_tipo', 'regular')
            component = ExtraMilkDecorator(component, milk_type)

        if 'extra_shot' in extras_dict and extras_dict['extra_shot']:
            shots = extras_dict.get('shots', 1)
            component = ExtraShotDecorator(component, shots)

        if 'queso' in extras_dict and extras_dict['queso']:
            component = ExtraCheeseDecorator(component)

        if 'aguacate' in extras_dict and extras_dict['aguacate']:
            component = ExtraAvocadoDecorator(component)

        if 'proteina_extra' in extras_dict and extras_dict['proteina_extra']:
            protein_type = extras_dict.get('proteina_tipo', 'pollo')
            component = ExtraProteinDecorator(component, protein_type)

        if 'tamaño' in extras_dict:
            component = SizeDecorator(component, extras_dict['tamaño'])

        if 'hielo' in extras_dict:
            component = IceLevelDecorator(component, extras_dict['hielo'])

        if 'azucar' in extras_dict:
            sweetener_type = extras_dict.get('azucar_tipo', 'azucar')
            level = extras_dict.get('azucar_nivel', 'normal')
            component = SweetenerDecorator(component, sweetener_type, level)

        if 'toppings' in extras_dict and extras_dict['toppings']:
            component = ToppingDecorator(component, extras_dict['toppings'])

        return component

    @staticmethod
    def get_decorated_info(product, extras_dict):
        """
        Obtener información completa del producto decorado

        Returns:
            dict con nombre, precio, descripción y tiempo
        """
        decorated = DecoratorFactory.apply_extras(product, extras_dict)

        return {
            'name': decorated.get_name(),
            'price': float(decorated.get_price()),
            'description': decorated.get_description(),
            'preparation_time': decorated.get_preparation_time(),
            'base_price': float(product.base_price),
            'extras_applied': list(extras_dict.keys())
        }