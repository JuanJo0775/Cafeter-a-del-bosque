# apps/core/service_registry.py
"""
ServiceRegistry simple para centralizar servicios del dominio.
No cambia implementaciones existentes: solo agrupa instancias.
"""

from apps.orders.services import OrderService
from apps.menu.services import MenuService
from apps.notifications.services import NotificationService
from apps.kitchen.handlers import KitchenRouter
from apps.core.config import get_config


class ServiceRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Instanciar servicios que ya existen en el proyecto
        self.config = get_config()
        self.orders = OrderService()
        # MenuService debe existir en apps/menu/services.py (según tu README/arquitectura)
        self.menu = MenuService()
        self.notifications = NotificationService()
        self.kitchen = KitchenRouter()

    def as_dict(self):
        """Útil para debugging"""
        return {
            'config': self.config,
            'orders': self.orders,
            'menu': self.menu,
            'notifications': self.notifications,
            'kitchen': self.kitchen,
        }


def get_registry():
    """Helper global para obtener el singleton del registry"""
    return ServiceRegistry()
