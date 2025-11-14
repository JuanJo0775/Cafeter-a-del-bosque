"""
ABSTRACT FACTORY: Familias completas de menús por temporada
"""
from abc import ABC, abstractmethod
from apps.menu.models import Product, Category


class AbstractMenuFactory(ABC):
    """
    Abstract Factory para crear familias de productos por temporada
    """

    @abstractmethod
    def create_hot_beverages(self):
        """Crear bebidas calientes de la temporada"""
        pass

    @abstractmethod
    def create_cold_beverages(self):
        """Crear bebidas frías de la temporada"""
        pass

    @abstractmethod
    def create_main_dishes(self):
        """Crear platos principales de la temporada"""
        pass

    @abstractmethod
    def create_desserts(self):
        """Crear postres de la temporada"""
        pass

    @abstractmethod
    def create_entries(self):
        """Crear entradas de la temporada"""
        pass

    @abstractmethod
    def get_season_name(self):
        """Nombre de la temporada"""
        pass


class RegularMenuFactory(AbstractMenuFactory):
    """Factory para menú regular (productos permanentes)"""

    def create_hot_beverages(self):
        """Bebidas calientes regulares"""
        cat = Category.objects.get_or_create(
            name='Bebidas Calientes',
            category_type='BEBIDAS'
        )[0]

        return Product.objects.filter(
            category__category_type='BEBIDAS',
            season__isnull=True,
            name__icontains='caliente'
        ) | Product.objects.filter(
            category__category_type='BEBIDAS',
            season__isnull=True,
            name__icontains='café'
        )

    def create_cold_beverages(self):
        """Bebidas frías regulares"""
        return Product.objects.filter(
            category__category_type='BEBIDAS',
            season__isnull=True,
            name__icontains='frí'
        ) | Product.objects.filter(
            category__category_type='BEBIDAS',
            season__isnull=True,
            name__icontains='jugo'
        )

    def create_main_dishes(self):
        """Platos principales regulares"""
        return Product.objects.filter(
            category__category_type='COMIDAS',
            season__isnull=True
        )

    def create_desserts(self):
        """Postres regulares"""
        return Product.objects.filter(
            category__category_type='POSTRES',
            season__isnull=True
        )

    def create_entries(self):
        """Entradas regulares"""
        return Product.objects.filter(
            category__category_type='ENTRADAS',
            season__isnull=True
        )

    def get_season_name(self):
        return 'REGULAR'


class WinterMenuFactory(AbstractMenuFactory):
    """Factory para menú de invierno"""

    def create_hot_beverages(self):
        """Bebidas calientes + especiales de invierno"""
        regular = Product.objects.filter(
            category__category_type='BEBIDAS',
            season__isnull=True
        ).filter(name__icontains='caliente') | Product.objects.filter(
            category__category_type='BEBIDAS',
            season__isnull=True,
            name__icontains='chocolate'
        )

        seasonal = Product.objects.filter(
            category__category_type='BEBIDAS',
            season='INVIERNO'
        )

        return regular | seasonal

    def create_cold_beverages(self):
        """Menos bebidas frías en invierno"""
        return Product.objects.filter(
            category__category_type='BEBIDAS',
            season__isnull=True,
            name__icontains='natural'
        )

    def create_main_dishes(self):
        """Platos regulares + especiales de invierno"""
        regular = Product.objects.filter(
            category__category_type='COMIDAS',
            season__isnull=True
        )
        seasonal = Product.objects.filter(
            category__category_type='COMIDAS',
            season='INVIERNO'
        )
        return regular | seasonal

    def create_desserts(self):
        """Postres regulares + especiales de invierno"""
        regular = Product.objects.filter(
            category__category_type='POSTRES',
            season__isnull=True
        )
        seasonal = Product.objects.filter(
            category__category_type='POSTRES',
            season='INVIERNO'
        )
        return regular | seasonal

    def create_entries(self):
        """Entradas regulares"""
        return Product.objects.filter(
            category__category_type='ENTRADAS',
            season__isnull=True
        )

    def get_season_name(self):
        return 'INVIERNO'


class SummerMenuFactory(AbstractMenuFactory):
    """Factory para menú de verano"""

    def create_hot_beverages(self):
        """Solo cafés básicos en verano"""
        return Product.objects.filter(
            category__category_type='BEBIDAS',
            season__isnull=True,
            name__icontains='café'
        )

    def create_cold_beverages(self):
        """Énfasis en bebidas frías"""
        regular = Product.objects.filter(
            category__category_type='BEBIDAS',
            season__isnull=True
        ).filter(name__icontains='frí') | Product.objects.filter(
            category__category_type='BEBIDAS',
            season__isnull=True,
            name__icontains='jugo'
        )

        seasonal = Product.objects.filter(
            category__category_type='BEBIDAS',
            season='VERANO'
        )

        return regular | seasonal

    def create_main_dishes(self):
        """Platos ligeros de verano"""
        regular = Product.objects.filter(
            category__category_type='COMIDAS',
            season__isnull=True,
            name__icontains='ensalada'
        )
        seasonal = Product.objects.filter(
            category__category_type='COMIDAS',
            season='VERANO'
        )
        return regular | seasonal

    def create_desserts(self):
        """Postres fríos de verano"""
        regular = Product.objects.filter(
            category__category_type='POSTRES',
            season__isnull=True
        )
        seasonal = Product.objects.filter(
            category__category_type='POSTRES',
            season='VERANO'
        )
        return regular | seasonal

    def create_entries(self):
        return Product.objects.filter(
            category__category_type='ENTRADAS',
            season__isnull=True
        )

    def get_season_name(self):
        return 'VERANO'


class AutumnMenuFactory(AbstractMenuFactory):
    """Factory para menú de otoño"""

    def create_hot_beverages(self):
        regular = Product.objects.filter(
            category__category_type='BEBIDAS',
            season__isnull=True
        )
        seasonal = Product.objects.filter(
            category__category_type='BEBIDAS',
            season='OTONIO'
        )
        return regular | seasonal

    def create_cold_beverages(self):
        return Product.objects.filter(
            category__category_type='BEBIDAS',
            season__isnull=True,
            name__icontains='natural'
        )

    def create_main_dishes(self):
        regular = Product.objects.filter(
            category__category_type='COMIDAS',
            season__isnull=True
        )
        seasonal = Product.objects.filter(
            category__category_type='COMIDAS',
            season='OTONIO'
        )
        return regular | seasonal

    def create_desserts(self):
        regular = Product.objects.filter(
            category__category_type='POSTRES',
            season__isnull=True
        )
        seasonal = Product.objects.filter(
            category__category_type='POSTRES',
            season='OTONIO'
        )
        return regular | seasonal

    def create_entries(self):
        return Product.objects.filter(
            category__category_type='ENTRADAS',
            season__isnull=True
        )

    def get_season_name(self):
        return 'OTONIO'


class SpringMenuFactory(AbstractMenuFactory):
    """Factory para menú de primavera"""

    def create_hot_beverages(self):
        return Product.objects.filter(
            category__category_type='BEBIDAS',
            season__isnull=True
        ).filter(name__icontains='café') | Product.objects.filter(
            category__category_type='BEBIDAS',
            season='PRIMAVERA'
        )

    def create_cold_beverages(self):
        regular = Product.objects.filter(
            category__category_type='BEBIDAS',
            season__isnull=True
        )
        seasonal = Product.objects.filter(
            category__category_type='BEBIDAS',
            season='PRIMAVERA'
        )
        return regular | seasonal

    def create_main_dishes(self):
        regular = Product.objects.filter(
            category__category_type='COMIDAS',
            season__isnull=True
        )
        seasonal = Product.objects.filter(
            category__category_type='COMIDAS',
            season='PRIMAVERA'
        )
        return regular | seasonal

    def create_desserts(self):
        regular = Product.objects.filter(
            category__category_type='POSTRES',
            season__isnull=True
        )
        seasonal = Product.objects.filter(
            category__category_type='POSTRES',
            season='PRIMAVERA'
        )
        return regular | seasonal

    def create_entries(self):
        return Product.objects.filter(
            category__category_type='ENTRADAS',
            season__isnull=True
        )

    def get_season_name(self):
        return 'PRIMAVERA'


def get_menu_factory_by_season(season='REGULAR'):
    """
    Obtener factory según temporada

    Args:
        season: 'REGULAR', 'INVIERNO', 'VERANO', 'OTONIO', 'PRIMAVERA'

    Returns:
        AbstractMenuFactory apropiado
    """
    factories = {
        'REGULAR': RegularMenuFactory(),
        'INVIERNO': WinterMenuFactory(),
        'VERANO': SummerMenuFactory(),
        'OTONIO': AutumnMenuFactory(),
        'PRIMAVERA': SpringMenuFactory()
    }

    return factories.get(season, RegularMenuFactory())