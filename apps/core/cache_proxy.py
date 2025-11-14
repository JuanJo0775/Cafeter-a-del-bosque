"""
Patrón PROXY - Cache del menú para evitar consultas repetitivas a BD
"""
from datetime import datetime, timedelta
from apps.menu.models import Product, Category


class MenuProxy:
    """
    Proxy que cachea el menú para evitar consultas constantes a BD
    Implementa Singleton interno para mantener cache único
    """

    _instance = None
    _cache = None
    _cache_timestamp = None
    _cache_duration = timedelta(minutes=15)  # Cache válido por 15 minutos

    # Estadísticas internas
    _cache_hits = 0
    _cache_misses = 0

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ==============================================================
    # MÉTODO PRINCIPAL: obtener menú (con estadísticas)
    # ==============================================================

    def get_menu(self, force_refresh=False):
        """
        Obtener menú desde cache o BD (con estadísticas)
        """
        if force_refresh or self._is_cache_expired():
            self.increment_cache_miss()
            self._refresh_cache()
        else:
            self.increment_cache_hit()

        return self._cache

    # ==============================================================
    # UTILIDADES INTERNAS
    # ==============================================================

    def _is_cache_expired(self):
        """Verificar si el cache expiró"""
        if self._cache is None or self._cache_timestamp is None:
            return True

        elapsed = datetime.now() - self._cache_timestamp
        return elapsed > self._cache_duration

    def _refresh_cache(self):
        """Recargar menú desde BD"""
        print("[PROXY] Cargando menú desde base de datos...")

        categories = Category.objects.prefetch_related('products').all()

        menu_data = []
        for category in categories:
            menu_data.append({
                'id': category.id,
                'name': category.name,
                'type': category.category_type,
                'description': category.description,
                'products': [
                    {
                        'id': product.id,
                        'name': product.name,
                        'description': product.description,
                        'base_price': float(product.base_price),
                        'preparation_time': product.preparation_time,
                        'available_extras': product.available_extras,
                        'is_available': product.is_available
                    }
                    for product in category.products.filter(is_available=True)
                ]
            })

        self._cache = menu_data
        self._cache_timestamp = datetime.now()
        print(f"[PROXY] Cache actualizado: {len(menu_data)} categorías")

    def invalidate_cache(self):
        """Invalidar cache manualmente"""
        self._cache = None
        self._cache_timestamp = None
        print("[PROXY] Cache invalidado")

    # ==============================================================
    # INFORMACIÓN Y ESTADÍSTICAS DEL CACHE
    # ==============================================================

    def get_cache_info(self):
        """Obtener información del estado del cache"""
        if self._cache_timestamp:
            age = datetime.now() - self._cache_timestamp
            return {
                'cached': True,
                'age_seconds': int(age.total_seconds()),
                'expires_in_seconds': int((self._cache_duration - age).total_seconds()),
                'items_count': len(self._cache) if self._cache else 0
            }
        return {
            'cached': False,
            'age_seconds': 0,
            'expires_in_seconds': 0,
            'items_count': 0
        }

    def get_statistics(self):
        """Obtener estadísticas del proxy"""
        return {
            'cache_info': self.get_cache_info(),
            'total_products': Product.objects.filter(is_available=True).count(),
            'total_categories': Category.objects.count(),
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses
        }

    # ==============================================================
    # CONTADORES DE HITS Y MISSES
    # ==============================================================

    def increment_cache_hit(self):
        """Incrementar contador de hits"""
        self._cache_hits += 1

    def increment_cache_miss(self):
        """Incrementar contador de misses"""
        self._cache_misses += 1

    # ==============================================================
    # BÚSQUEDA EN CACHE
    # ==============================================================

    def search_products(self, query):
        """
        Buscar productos en el cache

        Args:
            query: término de búsqueda

        Returns:
            Lista de productos que coinciden
        """
        if self._is_cache_expired():
            self._refresh_cache()

        results = []
        query_lower = query.lower()

        for category in self._cache:
            for product in category['products']:
                if (query_lower in product['name'].lower() or
                        query_lower in product['description'].lower()):
                    results.append({
                        **product,
                        'category': category['name']
                    })

        return results
