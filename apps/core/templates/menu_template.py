"""
TEMPLATE METHOD: Plantillas para construcción de menús
"""
from abc import ABC, abstractmethod


class MenuBuildTemplate(ABC):
    """
    Plantilla abstracta para construir menús
    """

    def build_menu(self, season=None):
        """
        Método template para construir menú completo

        Args:
            season: temporada opcional

        Returns:
            dict con menú construido
        """
        print(f"\n[MENU TEMPLATE] === Construyendo menú ===")

        # 1. Inicializar menú
        menu = self.initialize_menu(season)

        # 2. Cargar productos base
        base_products = self.load_base_products()
        menu['base_products'] = base_products

        # 3. Cargar productos de temporada (si aplica)
        if self.has_seasonal_products():
            seasonal_products = self.load_seasonal_products(season)
            menu['seasonal_products'] = seasonal_products

        # 4. Organizar por categorías
        menu['categories'] = self.organize_by_categories(
            base_products,
            menu.get('seasonal_products', [])
        )

        # 5. Aplicar estrategia de precios
        menu['categories'] = self.apply_pricing_strategy(menu['categories'], season)

        # 6. Filtrar productos no disponibles
        menu['categories'] = self.filter_available(menu['categories'])

        # 7. Agregar metadata
        menu['metadata'] = self.add_metadata(season)

        # 8. Post-procesamiento (hook)
        self.post_process(menu)

        print(f"[MENU TEMPLATE] === Menú construido ===\n")

        return menu

    # Métodos abstractos

    @abstractmethod
    def load_base_products(self):
        """Cargar productos base"""
        pass

    @abstractmethod
    def organize_by_categories(self, base_products, seasonal_products):
        """Organizar productos por categorías"""
        pass

    # Métodos concretos

    def initialize_menu(self, season):
        """Inicializar estructura del menú"""
        print(f"[MENU TEMPLATE] Inicializando menú - Temporada: {season}")

        return {
            'season': season,
            'base_products': [],
            'seasonal_products': [],
            'categories': {},
            'metadata': {}
        }

    def has_seasonal_products(self):
        """Hook: determinar si incluir productos de temporada"""
        return True

    def load_seasonal_products(self, season):
        """Cargar productos de temporada"""
        print(f"[MENU TEMPLATE] Cargando productos de temporada: {season}")

        from apps.menu.models import Product

        if not season:
            return []

        products = Product.objects.filter(
            season=season,
            is_available=True
        )

        return list(products.values('id', 'name', 'base_price', 'category__name', 'season'))

    def apply_pricing_strategy(self, categories, season):
        """Aplicar estrategia de precios según temporada"""
        print(f"[MENU TEMPLATE] Aplicando estrategia de precios")

        from apps.menu.strategies.pricing_strategy import get_pricing_strategy_for_season, PricingContext

        strategy = get_pricing_strategy_for_season(season or 'REGULAR')
        context = PricingContext(strategy)

        # Aplicar a cada categoría
        for category_name, category_data in categories.items():
            for product in category_data.get('products', []):
                # Obtener producto real para aplicar estrategia
                from apps.menu.models import Product
                try:
                    prod = Product.objects.get(id=product['id'])
                    price_info = context.get_price_info(prod)
                    product['final_price'] = price_info['final_price']
                    product['discount'] = price_info['discount_percentage']
                except Product.DoesNotExist:
                    pass

        return categories

    def filter_available(self, categories):
        """Filtrar solo productos disponibles"""
        print(f"[MENU TEMPLATE] Filtrando productos disponibles")

        filtered = {}
        for category_name, category_data in categories.items():
            available_products = [
                p for p in category_data.get('products', [])
                if p.get('is_available', True)
            ]

            if available_products:
                filtered[category_name] = {
                    **category_data,
                    'products': available_products
                }

        return filtered

    def add_metadata(self, season):
        """Agregar metadata al menú"""
        from datetime import datetime

        return {
            'generated_at': datetime.now().isoformat(),
            'season': season,
            'version': '1.0'
        }

    def post_process(self, menu):
        """Hook: post-procesamiento del menú"""
        pass


class StandardMenuBuildTemplate(MenuBuildTemplate):
    """
    Template para menú estándar
    """

    def load_base_products(self):
        """Cargar productos permanentes"""
        print("[STANDARD MENU] Cargando productos base")

        from apps.menu.models import Product

        products = Product.objects.filter(
            season__isnull=True,
            is_available=True
        ).select_related('category')

        return list(products.values(
            'id', 'name', 'description', 'base_price',
            'category__name', 'category__category_type',
            'preparation_time', 'is_available'
        ))

    def organize_by_categories(self, base_products, seasonal_products):
        """Organizar por categorías estándar"""
        print("[STANDARD MENU] Organizando por categorías")

        categories = {}

        all_products = base_products + seasonal_products

        for product in all_products:
            category_name = product.get('category__name', 'Sin categoría')

            if category_name not in categories:
                categories[category_name] = {
                    'type': product.get('category__category_type', 'GENERAL'),
                    'products': []
                }

            categories[category_name]['products'].append(product)

        return categories


class SeasonalMenuBuildTemplate(MenuBuildTemplate):
    """
    Template para menú de temporada
    Prioriza productos estacionales
    """

    def load_base_products(self):
        """Cargar solo productos base relevantes"""
        print("[SEASONAL MENU] Cargando productos base relevantes")

        from apps.menu.models import Product

        # Solo cargar productos básicos
        products = Product.objects.filter(
            season__isnull=True,
            is_available=True,
            category__category_type__in=['BEBIDAS', 'ENTRADAS']
        ).select_related('category')

        return list(products.values(
            'id', 'name', 'description', 'base_price',
            'category__name', 'category__category_type',
            'preparation_time', 'is_available'
        ))

    def organize_by_categories(self, base_products, seasonal_products):
        """Organizar priorizando productos de temporada"""
        print("[SEASONAL MENU] Organizando con prioridad estacional")

        categories = {}

        # Primero productos de temporada
        for product in seasonal_products:
            category_name = f"⭐ {product.get('category__name', 'Especiales de Temporada')}"

            if category_name not in categories:
                categories[category_name] = {
                    'type': 'SEASONAL',
                    'priority': 'high',
                    'products': []
                }

            categories[category_name]['products'].append(product)

        # Luego productos base
        for product in base_products:
            category_name = product.get('category__name', 'Sin categoría')

            if category_name not in categories:
                categories[category_name] = {
                    'type': product.get('category__category_type', 'GENERAL'),
                    'priority': 'normal',
                    'products': []
                }

            categories[category_name]['products'].append(product)

        return categories

    def post_process(self, menu):
        """Agregar información de temporada"""
        print("[SEASONAL MENU] Post-procesamiento estacional")

        menu['metadata']['is_seasonal'] = True
        menu['metadata']['seasonal_items_count'] = len(menu.get('seasonal_products', []))


class QuickMenuBuildTemplate(MenuBuildTemplate):
    """
    Template para menú rápido (productos de preparación rápida)
    """

    def load_base_products(self):
        """Cargar solo productos rápidos"""
        print("[QUICK MENU] Cargando productos de preparación rápida")

        from apps.menu.models import Product

        products = Product.objects.filter(
            preparation_time__lte=10,  # 10 minutos o menos
            is_available=True
        ).select_related('category')

        return list(products.values(
            'id', 'name', 'description', 'base_price',
            'category__name', 'category__category_type',
            'preparation_time', 'is_available'
        ))

    def organize_by_categories(self, base_products, seasonal_products):
        """Organizar por tiempo de preparación"""
        print("[QUICK MENU] Organizando por velocidad")

        categories = {
            'Express (≤5 min)': {'type': 'EXPRESS', 'products': []},
            'Rápido (6-10 min)': {'type': 'QUICK', 'products': []}
        }

        all_products = base_products + seasonal_products

        for product in all_products:
            prep_time = product.get('preparation_time', 0)

            if prep_time <= 5:
                categories['Express (≤5 min)']['products'].append(product)
            else:
                categories['Rápido (6-10 min)']['products'].append(product)

        return categories

    def has_seasonal_products(self):
        """No incluir productos de temporada en menú rápido"""
        return False


def get_menu_build_template(menu_type='standard'):
    """
    Factory para obtener template de menú

    Args:
        menu_type: 'standard', 'seasonal', 'quick'

    Returns:
        MenuBuildTemplate apropiado
    """
    templates = {
        'standard': StandardMenuBuildTemplate(),
        'seasonal': SeasonalMenuBuildTemplate(),
        'quick': QuickMenuBuildTemplate()
    }

    return templates.get(menu_type, StandardMenuBuildTemplate())