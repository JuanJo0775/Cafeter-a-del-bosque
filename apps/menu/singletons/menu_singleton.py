"""
SINGLETON: Instancia única del menú actual según temporada
"""
from datetime import datetime


class MenuSingleton:
    """
    Singleton que mantiene el menú activo según temporada
    Solo puede existir una instancia
    """

    _instance = None
    _current_season = None
    _menu_factory = None
    _last_update = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Inicializar con temporada actual"""
        self._current_season = self._detect_current_season()
        self._update_menu_factory()
        self._last_update = datetime.now()
        print(f"[SINGLETON] Menú inicializado - Temporada: {self._current_season}")

    def _detect_current_season(self):
        """
        Detectar temporada actual según fecha

        Returns:
            str con temporada
        """
        month = datetime.now().month

        # Colombia: temporadas invertidas (hemisferio norte)
        if month in [12, 1, 2]:
            return 'INVIERNO'
        elif month in [3, 4, 5]:
            return 'PRIMAVERA'
        elif month in [6, 7, 8]:
            return 'VERANO'
        elif month in [9, 10, 11]:
            return 'OTONIO'

        return 'REGULAR'

    def _update_menu_factory(self):
        """Actualizar factory según temporada"""
        from apps.menu.factories.abstract_menu_factory import get_menu_factory_by_season
        self._menu_factory = get_menu_factory_by_season(self._current_season)

    def get_current_season(self):
        """Obtener temporada actual"""
        return self._current_season

    def set_season(self, season):
        """
        Cambiar temporada manualmente (para eventos especiales)

        Args:
            season: 'REGULAR', 'INVIERNO', 'VERANO', 'OTONIO', 'PRIMAVERA'
        """
        valid_seasons = ['REGULAR', 'INVIERNO', 'VERANO', 'OTONIO', 'PRIMAVERA']

        if season not in valid_seasons:
            raise ValueError(f"Temporada inválida. Use: {valid_seasons}")

        self._current_season = season
        self._update_menu_factory()
        self._last_update = datetime.now()

        print(f"[SINGLETON] Temporada cambiada a: {season}")

    def get_menu_factory(self):
        """Obtener factory del menú actual"""
        return self._menu_factory

    def get_hot_beverages(self):
        """Obtener bebidas calientes de la temporada actual"""
        return self._menu_factory.create_hot_beverages()

    def get_cold_beverages(self):
        """Obtener bebidas frías de la temporada actual"""
        return self._menu_factory.create_cold_beverages()

    def get_main_dishes(self):
        """Obtener platos principales de la temporada actual"""
        return self._menu_factory.create_main_dishes()

    def get_desserts(self):
        """Obtener postres de la temporada actual"""
        return self._menu_factory.create_desserts()

    def get_entries(self):
        """Obtener entradas de la temporada actual"""
        return self._menu_factory.create_entries()

    def get_complete_menu(self):
        """
        Obtener menú completo según temporada actual

        Returns:
            dict con todas las categorías
        """
        return {
            'season': self._current_season,
            'last_update': self._last_update.isoformat(),
            'categories': {
                'hot_beverages': list(self.get_hot_beverages().values('id', 'name', 'base_price', 'season')),
                'cold_beverages': list(self.get_cold_beverages().values('id', 'name', 'base_price', 'season')),
                'main_dishes': list(self.get_main_dishes().values('id', 'name', 'base_price', 'season')),
                'desserts': list(self.get_desserts().values('id', 'name', 'base_price', 'season')),
                'entries': list(self.get_entries().values('id', 'name', 'base_price', 'season'))
            }
        }

    def refresh(self):
        """Refrescar menú (detectar temporada actual)"""
        old_season = self._current_season
        self._current_season = self._detect_current_season()

        if old_season != self._current_season:
            self._update_menu_factory()
            self._last_update = datetime.now()
            print(f"[SINGLETON] Temporada actualizada: {old_season} -> {self._current_season}")
        else:
            print(f"[SINGLETON] Temporada sin cambios: {self._current_season}")

    def get_info(self):
        """Obtener información del singleton"""
        return {
            'current_season': self._current_season,
            'last_update': self._last_update.isoformat() if self._last_update else None,
            'factory_type': type(self._menu_factory).__name__
        }


def get_menu_singleton():
    """Helper para obtener instancia única del menú"""
    return MenuSingleton()