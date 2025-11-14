"""
FACTORY METHOD: Crear productos según categoría
"""
from abc import ABC, abstractmethod
from apps.menu.models import Product, Category
from decimal import Decimal


class ProductFactory(ABC):
    """Factory abstracto para crear productos"""

    @abstractmethod
    def create_product(self, name, description, base_price, preparation_time, **kwargs):
        pass

    def get_category_type(self):
        """Retorna el tipo de categoría que maneja esta factory"""
        return None


class BeverageProductFactory(ProductFactory):
    """Factory para crear bebidas"""

    def create_product(self, name, description, base_price, preparation_time, **kwargs):
        category = Category.objects.get(category_type='BEBIDAS', name=kwargs.get('category_name', 'Bebidas'))

        # Extras específicos de bebidas
        default_extras = {
            'leche': 0.5,
            'azucar': 0.0,
            'hielo': 0.0,
            'extra_shot': 1.0
        }

        extras = kwargs.get('available_extras', {})
        extras.update(default_extras)

        product = Product.objects.create(
            name=name,
            category=category,
            description=description,
            base_price=Decimal(str(base_price)),
            preparation_time=preparation_time,
            available_extras=extras,
            season=kwargs.get('season')
        )

        print(f"[FACTORY] Bebida creada: {product.name}")
        return product

    def get_category_type(self):
        return 'BEBIDAS'


class FoodProductFactory(ProductFactory):
    """Factory para crear comidas"""

    def create_product(self, name, description, base_price, preparation_time, **kwargs):
        category = Category.objects.get(category_type='COMIDAS', name=kwargs.get('category_name', 'Comidas'))

        # Extras específicos de comidas
        default_extras = {
            'queso': 0.5,
            'aguacate': 1.0,
            'proteina_extra': 2.0
        }

        extras = kwargs.get('available_extras', {})
        extras.update(default_extras)

        product = Product.objects.create(
            name=name,
            category=category,
            description=description,
            base_price=Decimal(str(base_price)),
            preparation_time=preparation_time,
            available_extras=extras,
            season=kwargs.get('season')
        )

        print(f"[FACTORY] Comida creada: {product.name}")
        return product

    def get_category_type(self):
        return 'COMIDAS'


class DessertProductFactory(ProductFactory):
    """Factory para crear postres"""

    def create_product(self, name, description, base_price, preparation_time, **kwargs):
        category = Category.objects.get(category_type='POSTRES', name=kwargs.get('category_name', 'Postres'))

        default_extras = {
            'crema': 0.5,
            'salsa_chocolate': 0.3,
            'helado': 1.0
        }

        extras = kwargs.get('available_extras', {})
        extras.update(default_extras)

        product = Product.objects.create(
            name=name,
            category=category,
            description=description,
            base_price=Decimal(str(base_price)),
            preparation_time=preparation_time,
            available_extras=extras,
            season=kwargs.get('season')
        )

        print(f"[FACTORY] Postre creado: {product.name}")
        return product

    def get_category_type(self):
        return 'POSTRES'


class EntryProductFactory(ProductFactory):
    """Factory para crear entradas"""

    def create_product(self, name, description, base_price, preparation_time, **kwargs):
        category = Category.objects.get(category_type='ENTRADAS', name=kwargs.get('category_name', 'Entradas'))

        default_extras = {
            'mantequilla': 0.2,
            'mermelada': 0.3
        }

        extras = kwargs.get('available_extras', {})
        extras.update(default_extras)

        product = Product.objects.create(
            name=name,
            category=category,
            description=description,
            base_price=Decimal(str(base_price)),
            preparation_time=preparation_time,
            available_extras=extras,
            season=kwargs.get('season')
        )

        print(f"[FACTORY] Entrada creada: {product.name}")
        return product

    def get_category_type(self):
        return 'ENTRADAS'


def get_product_factory(category_type):
    """
    Obtener factory según tipo de categoría

    Args:
        category_type: 'BEBIDAS', 'COMIDAS', 'POSTRES', 'ENTRADAS'

    Returns:
        ProductFactory apropiado
    """
    factories = {
        'BEBIDAS': BeverageProductFactory(),
        'COMIDAS': FoodProductFactory(),
        'POSTRES': DessertProductFactory(),
        'ENTRADAS': EntryProductFactory()
    }

    return factories.get(category_type, BeverageProductFactory())