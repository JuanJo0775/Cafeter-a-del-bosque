"""
Patrón SINGLETON - Configuración única del sistema
"""


class CafeteriaConfig:
    """
    Singleton para configuración global de la cafetería
    Solo debe existir una instancia de configuración
    """

    _instance = None
    _config = {
        'max_tables': 20,
        'max_items_per_order': 50,
        'kitchen_capacity': 10,
        'enable_notifications': True,
        'tax_rate': 0.19,  # 19% IVA Colombia
        'service_charge': 0.10,  # 10% servicio
        'opening_time': '07:00',
        'closing_time': '22:00',
        'cache_duration_minutes': 15,
        'max_preparation_time_minutes': 60
    }

    def __new__(cls):
        """Asegurar que solo exista una instancia"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            print("[SINGLETON] Configuración inicializada")
        return cls._instance

    def get_config(self):
        """Obtener toda la configuración"""
        return self._config.copy()

    def get(self, key, default=None):
        """Obtener un valor de configuración"""
        return self._config.get(key, default)

    def set(self, key, value):
        """Establecer un valor de configuración"""
        self._config[key] = value
        print(f"[CONFIG] {key} = {value}")

    def update_config(self, **kwargs):
        """Actualizar múltiples valores"""
        for key, value in kwargs.items():
            if key in self._config:
                self._config[key] = value
                print(f"[CONFIG] {key} actualizado")

    def reset_to_defaults(self):
        """Restaurar configuración por defecto"""
        self._config = {
            'max_tables': 20,
            'max_items_per_order': 50,
            'kitchen_capacity': 10,
            'enable_notifications': True,
            'tax_rate': 0.19,
            'service_charge': 0.10,
            'opening_time': '07:00',
            'closing_time': '22:00',
            'cache_duration_minutes': 15,
            'max_preparation_time_minutes': 60
        }
        print("[CONFIG] Configuración restaurada a valores por defecto")


# Función helper para obtener la instancia
def get_config():
    """Obtener instancia única de configuración"""
    return CafeteriaConfig()