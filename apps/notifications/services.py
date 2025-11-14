"""
Patrón OBSERVER para notificaciones
"""
from abc import ABC, abstractmethod
from datetime import datetime


class Observer(ABC):
    """Observer abstracto"""

    @abstractmethod
    def update(self, subject, event, data):
        """Recibir notificación"""
        pass


class Subject:
    """Subject que notifica a observers"""

    def __init__(self):
        self._observers = []

    def attach(self, observer: Observer):
        """Agregar observer"""
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: Observer):
        """Remover observer"""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, event, data):
        """Notificar a todos los observers"""
        for observer in self._observers:
            observer.update(self, event, data)


class WaiterObserver(Observer):
    """Observer para meseros"""

    def __init__(self, waiter):
        self.waiter = waiter
        self.notifications = []

    def update(self, subject, event, data):
        """Recibir notificación"""
        notification = {
            'timestamp': datetime.now().isoformat(),
            'event': event,
            'data': data,
            'waiter': self.waiter.username
        }
        self.notifications.append(notification)

        print(f"[MESERO {self.waiter.username}] {event}: Orden #{data.get('order_id')} - Mesa {data.get('table')}")

    def get_notifications(self):
        return self.notifications


class KitchenObserver(Observer):
    """Observer para cocina"""

    def __init__(self):
        self.notifications = []

    def update(self, subject, event, data):
        """Recibir notificación de nueva orden"""
        notification = {
            'timestamp': datetime.now().isoformat(),
            'event': event,
            'data': data
        }
        self.notifications.append(notification)

        print(f"[COCINA] {event}: Orden #{data.get('order_id')} - {data.get('items_count')} items")

    def get_notifications(self):
        return self.notifications


class NotificationService:
    """Servicio de notificaciones - Singleton Subject"""

    _instance = None
    _subject = Subject()
    _kitchen_observer = KitchenObserver()
    _waiter_observers = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Siempre agregar observer de cocina
            cls._subject.attach(cls._kitchen_observer)
        return cls._instance

    @classmethod
    def register_waiter(cls, waiter):
        """Registrar mesero como observer"""
        if waiter.id not in cls._waiter_observers:
            observer = WaiterObserver(waiter)
            cls._waiter_observers[waiter.id] = observer
            cls._subject.attach(observer)

    @classmethod
    def unregister_waiter(cls, waiter):
        """Desregistrar mesero"""
        if waiter.id in cls._waiter_observers:
            observer = cls._waiter_observers[waiter.id]
            cls._subject.detach(observer)
            del cls._waiter_observers[waiter.id]

    @classmethod
    def notify_kitchen(cls, order):
        """Notificar a cocina sobre nueva orden"""
        cls._subject.notify('NEW_ORDER', {
            'order_id': order.id,
            'table': order.table_number,
            'items_count': order.items.count(),
            'customer': order.customer.username
        })

    @classmethod
    def notify_waiter(cls, order):
        """Notificar a mesero que orden está lista"""
        if order.mesero and order.mesero.id in cls._waiter_observers:
            observer = cls._waiter_observers[order.mesero.id]
            observer.update(cls._subject, 'ORDER_READY', {
                'order_id': order.id,
                'table': order.table_number
            })
        else:
            # Notificar a todos los meseros si no hay asignado
            for observer in cls._waiter_observers.values():
                observer.update(cls._subject, 'ORDER_READY', {
                    'order_id': order.id,
                    'table': order.table_number
                })

    @classmethod
    def get_waiter_notifications(cls, waiter):
        """Obtener notificaciones de un mesero"""
        if waiter.id in cls._waiter_observers:
            return cls._waiter_observers[waiter.id].get_notifications()
        return []

    @classmethod
    def get_kitchen_notifications(cls):
        """Obtener notificaciones de cocina"""
        return cls._kitchen_observer.get_notifications()