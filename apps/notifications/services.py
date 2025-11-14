"""
OBSERVER: Sistema de notificaciones con observers múltiples
Los observers se registran y reciben notificaciones automáticas
"""
from abc import ABC, abstractmethod
from datetime import datetime
from collections import defaultdict


class Observer(ABC):
    """Observer abstracto para recibir notificaciones"""

    def __init__(self, observer_id, name):
        self.observer_id = observer_id
        self.name = name
        self.notifications = []

    @abstractmethod
    def update(self, subject, event, data):
        """
        Recibir notificación

        Args:
            subject: Subject que notifica
            event: tipo de evento
            data: datos del evento
        """
        pass

    def get_notifications(self):
        """Obtener todas las notificaciones"""
        return self.notifications

    def clear_notifications(self):
        """Limpiar notificaciones"""
        self.notifications = []

    def get_unread_count(self):
        """Contar notificaciones no leídas"""
        return len([n for n in self.notifications if not n.get('read', False)])

    def mark_as_read(self, notification_id):
        """Marcar notificación como leída"""
        for notif in self.notifications:
            if notif.get('id') == notification_id:
                notif['read'] = True


class Subject:
    """
    Subject que mantiene lista de observers y los notifica
    """

    def __init__(self):
        self._observers = []

    def attach(self, observer: Observer):
        """
        Agregar observer

        Args:
            observer: Observer a agregar
        """
        if observer not in self._observers:
            self._observers.append(observer)
            print(f"[SUBJECT] Observer registrado: {observer.name}")

    def detach(self, observer: Observer):
        """
        Remover observer

        Args:
            observer: Observer a remover
        """
        if observer in self._observers:
            self._observers.remove(observer)
            print(f"[SUBJECT] Observer desregistrado: {observer.name}")

    def notify(self, event, data):
        """
        Notificar a todos los observers

        Args:
            event: tipo de evento
            data: datos del evento
        """
        print(f"[SUBJECT] Notificando evento '{event}' a {len(self._observers)} observer(s)")

        for observer in self._observers:
            try:
                observer.update(self, event, data)
            except Exception as e:
                print(f"[SUBJECT] Error notificando a {observer.name}: {e}")

    def get_observers_count(self):
        """Obtener cantidad de observers"""
        return len(self._observers)

    def get_observers_list(self):
        """Obtener lista de observers"""
        return [
            {
                'id': obs.observer_id,
                'name': obs.name,
                'type': type(obs).__name__
            }
            for obs in self._observers
        ]


class WaiterObserver(Observer):
    """Observer para meseros - recibe notificaciones de órdenes listas"""

    def __init__(self, waiter):
        super().__init__(waiter.id, f"Mesero: {waiter.username}")
        self.waiter = waiter

    def update(self, subject, event, data):
        """Recibir notificación de evento"""
        notification = {
            'id': f"{self.observer_id}_{len(self.notifications)}",
            'timestamp': datetime.now().isoformat(),
            'event': event,
            'data': data,
            'waiter_id': self.waiter.id,
            'waiter_name': self.waiter.username,
            'read': False,
            'priority': self._calculate_priority(event, data)
        }

        self.notifications.append(notification)

        # Log según tipo de evento
        if event == 'ORDER_READY':
            print(f"[MESERO {self.waiter.username}] 🔔 Orden #{data.get('order_id')} LISTA - Mesa {data.get('table')}")
        elif event == 'ORDER_ASSIGNED':
            print(f"[MESERO {self.waiter.username}] 📋 Nueva orden asignada #{data.get('order_id')} - Mesa {data.get('table')}")
        elif event == 'ORDER_DELAYED':
            print(f"[MESERO {self.waiter.username}] ⚠️ Orden #{data.get('order_id')} RETRASADA")
        else:
            print(f"[MESERO {self.waiter.username}] 📨 {event}: {data}")

    def _calculate_priority(self, event, data):
        """Calcular prioridad de la notificación"""
        priority_map = {
            'ORDER_READY': 'high',
            'ORDER_DELAYED': 'high',
            'ORDER_ASSIGNED': 'medium',
            'ORDER_CANCELLED': 'low'
        }
        return priority_map.get(event, 'normal')

    def get_pending_orders(self):
        """Obtener órdenes pendientes de servir"""
        return [
            notif for notif in self.notifications
            if notif['event'] == 'ORDER_READY' and not notif['read']
        ]


class KitchenObserver(Observer):
    """Observer para cocina - recibe notificaciones de nuevas órdenes"""

    def __init__(self, kitchen_id="main_kitchen"):
        super().__init__(kitchen_id, "Cocina Principal")
        self.kitchen_id = kitchen_id

    def update(self, subject, event, data):
        """Recibir notificación de nueva orden"""
        notification = {
            'id': f"{self.observer_id}_{len(self.notifications)}",
            'timestamp': datetime.now().isoformat(),
            'event': event,
            'data': data,
            'kitchen_id': self.kitchen_id,
            'read': False,
            'priority': self._calculate_priority(event, data)
        }

        self.notifications.append(notification)

        # Log según evento
        if event == 'NEW_ORDER':
            items_count = data.get('items_count', 0)
            print(f"[COCINA] 🍳 Nueva orden #{data.get('order_id')} - Mesa {data.get('table')} - {items_count} items")
        elif event == 'ORDER_CANCELLED':
            print(f"[COCINA] ❌ Orden #{data.get('order_id')} CANCELADA")
        elif event == 'ORDER_MODIFIED':
            print(f"[COCINA] ⚠️ Orden #{data.get('order_id')} MODIFICADA")
        else:
            print(f"[COCINA] 📨 {event}: {data}")

    def _calculate_priority(self, event, data):
        """Calcular prioridad"""
        priority_map = {
            'NEW_ORDER': 'high',
            'ORDER_MODIFIED': 'high',
            'ORDER_CANCELLED': 'medium'
        }
        return priority_map.get(event, 'normal')

    def get_active_orders(self):
        """Obtener órdenes activas en cocina"""
        return [
            notif for notif in self.notifications
            if notif['event'] == 'NEW_ORDER' and not notif['read']
        ]


class ChefObserver(Observer):
    """Observer para cocineros individuales"""

    def __init__(self, chef):
        super().__init__(chef.id, f"Chef: {chef.username}")
        self.chef = chef
        self.assigned_station = None

    def set_station(self, station_type):
        """Asignar estación al chef"""
        self.assigned_station = station_type
        print(f"[CHEF {self.chef.username}] Asignado a estación: {station_type}")

    def update(self, subject, event, data):
        """Recibir notificación"""
        # Filtrar por estación si está asignada
        if self.assigned_station and data.get('station') != self.assigned_station:
            return  # No es para esta estación

        notification = {
            'id': f"{self.observer_id}_{len(self.notifications)}",
            'timestamp': datetime.now().isoformat(),
            'event': event,
            'data': data,
            'chef_id': self.chef.id,
            'chef_name': self.chef.username,
            'station': self.assigned_station,
            'read': False,
            'priority': 'high' if event == 'NEW_ORDER' else 'normal'
        }

        self.notifications.append(notification)

        print(f"[CHEF {self.chef.username}] 👨‍🍳 {event} - Orden #{data.get('order_id')}")


class CustomerObserver(Observer):
    """Observer para clientes - recibe actualizaciones de sus órdenes"""

    def __init__(self, customer):
        super().__init__(customer.id, f"Cliente: {customer.username}")
        self.customer = customer

    def update(self, subject, event, data):
        """Recibir notificación"""
        # Solo notificar eventos relevantes para el cliente
        relevant_events = [
            'ORDER_CONFIRMED',
            'ORDER_IN_PREPARATION',
            'ORDER_READY',
            'ORDER_DELIVERED',
            'ORDER_CANCELLED',
            'ORDER_DELAYED'
        ]

        if event not in relevant_events:
            return

        notification = {
            'id': f"{self.observer_id}_{len(self.notifications)}",
            'timestamp': datetime.now().isoformat(),
            'event': event,
            'data': data,
            'customer_id': self.customer.id,
            'customer_name': self.customer.username,
            'read': False,
            'priority': self._calculate_priority(event)
        }

        self.notifications.append(notification)

        # Mensajes amigables para el cliente
        messages = {
            'ORDER_CONFIRMED': f"✅ Tu orden #{data.get('order_id')} ha sido confirmada",
            'ORDER_IN_PREPARATION': f"👨‍🍳 Tu orden está siendo preparada",
            'ORDER_READY': f"🎉 ¡Tu orden está lista! Mesa {data.get('table')}",
            'ORDER_DELIVERED': f"✅ Orden entregada. ¡Buen provecho!",
            'ORDER_CANCELLED': f"❌ Tu orden fue cancelada",
            'ORDER_DELAYED': f"⏰ Tu orden se está demorando un poco más"
        }

        message = messages.get(event, f"{event}")
        print(f"[CLIENTE {self.customer.username}] {message}")

    def _calculate_priority(self, event):
        """Calcular prioridad"""
        high_priority = ['ORDER_READY', 'ORDER_CANCELLED', 'ORDER_DELAYED']
        return 'high' if event in high_priority else 'normal'


class NotificationService:
    """
    Servicio centralizado de notificaciones
    Implementa Singleton para mantener estado global
    """

    _instance = None
    _subject = None
    _kitchen_observer = None
    _waiter_observers = {}
    _chef_observers = {}
    _customer_observers = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Inicializar servicio"""
        self._subject = Subject()
        self._kitchen_observer = KitchenObserver()
        self._subject.attach(self._kitchen_observer)

        print("[NOTIFICATION SERVICE] Servicio inicializado")
        print("[NOTIFICATION SERVICE] Observer de cocina registrado por defecto")

    @classmethod
    def register_waiter(cls, waiter):
        """
        Registrar mesero como observer

        Args:
            waiter: User con role='MESERO'
        """
        if waiter.role != 'MESERO':
            raise ValueError("Usuario debe ser MESERO")

        if waiter.id not in cls._waiter_observers:
            observer = WaiterObserver(waiter)
            cls._waiter_observers[waiter.id] = observer
            cls._subject.attach(observer)
            print(f"[NOTIFICATION SERVICE] Mesero registrado: {waiter.username}")

    @classmethod
    def unregister_waiter(cls, waiter):
        """Desregistrar mesero"""
        if waiter.id in cls._waiter_observers:
            observer = cls._waiter_observers[waiter.id]
            cls._subject.detach(observer)
            del cls._waiter_observers[waiter.id]
            print(f"[NOTIFICATION SERVICE] Mesero desregistrado: {waiter.username}")

    @classmethod
    def register_chef(cls, chef, station_type=None):
        """
        Registrar cocinero como observer

        Args:
            chef: User con role='COCINERO'
            station_type: tipo de estación asignada
        """
        if chef.role != 'COCINERO':
            raise ValueError("Usuario debe ser COCINERO")

        if chef.id not in cls._chef_observers:
            observer = ChefObserver(chef)
            if station_type:
                observer.set_station(station_type)
            cls._chef_observers[chef.id] = observer
            cls._subject.attach(observer)
            print(f"[NOTIFICATION SERVICE] Chef registrado: {chef.username}")

    @classmethod
    def unregister_chef(cls, chef):
        """Desregistrar cocinero"""
        if chef.id in cls._chef_observers:
            observer = cls._chef_observers[chef.id]
            cls._subject.detach(observer)
            del cls._chef_observers[chef.id]
            print(f"[NOTIFICATION SERVICE] Chef desregistrado: {chef.username}")

    @classmethod
    def register_customer(cls, customer):
        """
        Registrar cliente como observer

        Args:
            customer: User con role='CLIENTE'
        """
        if customer.role != 'CLIENTE':
            raise ValueError("Usuario debe ser CLIENTE")

        if customer.id not in cls._customer_observers:
            observer = CustomerObserver(customer)
            cls._customer_observers[customer.id] = observer
            cls._subject.attach(observer)
            print(f"[NOTIFICATION SERVICE] Cliente registrado: {customer.username}")

    @classmethod
    def unregister_customer(cls, customer):
        """Desregistrar cliente"""
        if customer.id in cls._customer_observers:
            observer = cls._customer_observers[customer.id]
            cls._subject.detach(observer)
            del cls._customer_observers[customer.id]
            print(f"[NOTIFICATION SERVICE] Cliente desregistrado: {customer.username}")

    @classmethod
    def notify_new_order(cls, order):
        """
        Notificar nueva orden a cocina

        Args:
            order: instancia de Order
        """
        print(f"\n[NOTIFICATION SERVICE] === Notificando nueva orden #{order.id} ===")

        cls._subject.notify('NEW_ORDER', {
            'order_id': order.id,
            'table': order.table_number,
            'items_count': order.items.count(),
            'customer': order.customer.username,
            'total': float(order.total_price),
            'special_instructions': order.special_instructions
        })

    @classmethod
    def notify_order_ready(cls, order):
        """
        Notificar que orden está lista a mesero asignado

        Args:
            order: instancia de Order
        """
        print(f"\n[NOTIFICATION SERVICE] === Notificando orden lista #{order.id} ===")

        data = {
            'order_id': order.id,
            'table': order.table_number,
            'customer': order.customer.username
        }

        # Notificar a mesero específico si está asignado
        if order.mesero and order.mesero.id in cls._waiter_observers:
            observer = cls._waiter_observers[order.mesero.id]
            observer.update(cls._subject, 'ORDER_READY', data)
        else:
            # Notificar a todos los meseros
            cls._subject.notify('ORDER_READY', data)

        # Notificar al cliente
        if order.customer.id in cls._customer_observers:
            observer = cls._customer_observers[order.customer.id]
            observer.update(cls._subject, 'ORDER_READY', data)

    @classmethod
    def notify_order_delivered(cls, order):
        """Notificar que orden fue entregada"""
        print(f"\n[NOTIFICATION SERVICE] === Notificando orden entregada #{order.id} ===")

        data = {
            'order_id': order.id,
            'table': order.table_number,
            'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None
        }

        # Notificar al cliente
        if order.customer.id in cls._customer_observers:
            observer = cls._customer_observers[order.customer.id]
            observer.update(cls._subject, 'ORDER_DELIVERED', data)

    @classmethod
    def notify_order_cancelled(cls, order, reason=""):
        """Notificar cancelación de orden"""
        print(f"\n[NOTIFICATION SERVICE] === Notificando orden cancelada #{order.id} ===")

        data = {
            'order_id': order.id,
            'table': order.table_number,
            'reason': reason
        }

        cls._subject.notify('ORDER_CANCELLED', data)

    @classmethod
    def notify_order_modified(cls, order):
        """Notificar modificación de orden"""
        print(f"\n[NOTIFICATION SERVICE] === Notificando orden modificada #{order.id} ===")

        cls._subject.notify('ORDER_MODIFIED', {
            'order_id': order.id,
            'table': order.table_number,
            'items_count': order.items.count()
        })

    @classmethod
    def notify_order_delayed(cls, order):
        """Notificar orden retrasada"""
        print(f"\n[NOTIFICATION SERVICE] === Notificando orden retrasada #{order.id} ===")

        data = {
            'order_id': order.id,
            'table': order.table_number
        }

        # Notificar a mesero y cliente
        if order.mesero and order.mesero.id in cls._waiter_observers:
            observer = cls._waiter_observers[order.mesero.id]
            observer.update(cls._subject, 'ORDER_DELAYED', data)

        if order.customer.id in cls._customer_observers:
            observer = cls._customer_observers[order.customer.id]
            observer.update(cls._subject, 'ORDER_DELAYED', data)

    @classmethod
    def get_waiter_notifications(cls, waiter):
        """Obtener notificaciones de un mesero"""
        if waiter.id in cls._waiter_observers:
            return cls._waiter_observers[waiter.id].get_notifications()
        return []

    @classmethod
    def get_chef_notifications(cls, chef):
        """Obtener notificaciones de un chef"""
        if chef.id in cls._chef_observers:
            return cls._chef_observers[chef.id].get_notifications()
        return []

    @classmethod
    def get_customer_notifications(cls, customer):
        """Obtener notificaciones de un cliente"""
        if customer.id in cls._customer_observers:
            return cls._customer_observers[customer.id].get_notifications()
        return []

    @classmethod
    def get_kitchen_notifications(cls):
        """Obtener notificaciones de cocina"""
        return cls._kitchen_observer.get_notifications()

    @classmethod
    def get_service_stats(cls):
        """Obtener estadísticas del servicio"""
        return {
            'total_observers': cls._subject.get_observers_count(),
            'registered_waiters': len(cls._waiter_observers),
            'registered_chefs': len(cls._chef_observers),
            'registered_customers': len(cls._customer_observers),
            'kitchen_notifications': len(cls._kitchen_observer.get_notifications()),
            'observers_list': cls._subject.get_observers_list()
        }

    @classmethod
    def clear_all_notifications(cls):
        """Limpiar todas las notificaciones"""
        cls._kitchen_observer.clear_notifications()

        for observer in cls._waiter_observers.values():
            observer.clear_notifications()

        for observer in cls._chef_observers.values():
            observer.clear_notifications()

        for observer in cls._customer_observers.values():
            observer.clear_notifications()

        print("[NOTIFICATION SERVICE] Todas las notificaciones limpiadas")