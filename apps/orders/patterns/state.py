"""
Patrón STATE para gestionar ciclo de vida de órdenes
PENDIENTE → EN_PREPARACION → LISTO → ENTREGADO
"""
from abc import ABC, abstractmethod
from datetime import datetime


class OrderState(ABC):
    """Estado abstracto de una orden"""

    @abstractmethod
    def handle(self, order):
        """Manejar la orden en este estado"""
        pass

    @abstractmethod
    def next_state(self):
        """Obtener siguiente estado"""
        pass

    @abstractmethod
    def can_cancel(self):
        """¿Se puede cancelar en este estado?"""
        pass

    def get_name(self):
        """Nombre del estado"""
        return self.__class__.__name__.replace('State', '').upper()


class PendingState(OrderState):
    """Estado: Orden recién creada, pendiente de preparación"""

    def handle(self, order):
        """Acciones cuando la orden está pendiente"""
        print(f"[STATE] Orden #{order.id} está PENDIENTE. Esperando asignación a cocina.")
        order.status = 'PENDIENTE'
        order.save()

    def next_state(self):
        """Siguiente estado: En Preparación"""
        return InPreparationState()

    def can_cancel(self):
        return True

    def get_name(self):
        return 'PENDIENTE'


class InPreparationState(OrderState):
    """Estado: Orden asignada a cocina, en preparación"""

    def handle(self, order):
        """Acciones cuando la orden está en preparación"""
        print(f"[STATE] Orden #{order.id} EN_PREPARACION. Cocina trabajando.")
        order.status = 'EN_PREPARACION'
        order.save()

        # Notificar a cocina (Observer)
        from apps.notifications.services import NotificationService
        NotificationService.notify_kitchen(order)

    def next_state(self):
        """Siguiente estado: Listo"""
        return ReadyState()

    def can_cancel(self):
        return True

    def get_name(self):
        return 'EN_PREPARACION'


class ReadyState(OrderState):
    """Estado: Orden lista para servir"""

    def handle(self, order):
        """Acciones cuando la orden está lista"""
        print(f"[STATE] Orden #{order.id} LISTA. Notificando mesero.")
        order.status = 'LISTO'
        order.prepared_at = datetime.now()
        order.save()

        # Notificar a mesero (Observer)
        from apps.notifications.services import NotificationService
        NotificationService.notify_waiter(order)

    def next_state(self):
        """Siguiente estado: Entregado"""
        return DeliveredState()

    def can_cancel(self):
        return False

    def get_name(self):
        return 'LISTO'


class DeliveredState(OrderState):
    """Estado: Orden entregada al cliente"""

    def handle(self, order):
        """Acciones cuando la orden es entregada"""
        print(f"[STATE] Orden #{order.id} ENTREGADA. Proceso completado.")
        order.status = 'ENTREGADO'
        order.delivered_at = datetime.now()
        order.save()

    def next_state(self):
        """Estado final, no hay siguiente"""
        return None

    def can_cancel(self):
        return False

    def get_name(self):
        return 'ENTREGADO'


class CancelledState(OrderState):
    """Estado: Orden cancelada"""

    def handle(self, order):
        """Acciones cuando la orden es cancelada"""
        print(f"[STATE] Orden #{order.id} CANCELADA.")
        order.status = 'CANCELADO'
        order.save()

    def next_state(self):
        """Estado final, no hay siguiente"""
        return None

    def can_cancel(self):
        return False

    def get_name(self):
        return 'CANCELADO'


class OrderStateManager:
    """
    Gestor de estados de órdenes
    Coordina transiciones entre estados
    """

    # Mapeo de estados
    STATES = {
        'PENDIENTE': PendingState(),
        'EN_PREPARACION': InPreparationState(),
        'LISTO': ReadyState(),
        'ENTREGADO': DeliveredState(),
        'CANCELADO': CancelledState(),
    }

    @classmethod
    def get_state(cls, order):
        """Obtener estado actual de una orden"""
        return cls.STATES.get(order.status, PendingState())

    @classmethod
    def advance_order(cls, order):
        """
        Avanzar orden al siguiente estado

        Args:
            order: instancia de Order

        Returns:
            nuevo estado
        """
        current_state = cls.get_state(order)
        next_state = current_state.next_state()

        if next_state is None:
            raise ValueError(f"La orden está en estado final: {order.status}")

        # Aplicar nuevo estado
        next_state.handle(order)

        return next_state

    @classmethod
    def cancel_order(cls, order):
        """Cancelar orden si es posible"""
        current_state = cls.get_state(order)

        if not current_state.can_cancel():
            raise ValueError(f"No se puede cancelar orden en estado {order.status}")

        cancelled_state = CancelledState()
        cancelled_state.handle(order)

        return cancelled_state

    @classmethod
    def can_advance(cls, order):
        """Verificar si la orden puede avanzar"""
        current_state = cls.get_state(order)
        return current_state.next_state() is not None

    @classmethod
    def can_cancel(cls, order):
        """Verificar si la orden puede ser cancelada"""
        current_state = cls.get_state(order)
        return current_state.can_cancel()