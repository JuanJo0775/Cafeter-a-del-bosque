"""
STATE: Gestión completa del ciclo de vida de órdenes
Con validaciones, transiciones automáticas y notificaciones
"""
from abc import ABC, abstractmethod
from datetime import datetime


class OrderState(ABC):
    """Estado abstracto de una orden con validaciones"""

    @abstractmethod
    def handle(self, order):
        """Acciones al entrar en este estado"""
        pass

    @abstractmethod
    def next_state(self):
        """Obtener siguiente estado posible"""
        pass

    @abstractmethod
    def can_cancel(self):
        """¿Se puede cancelar en este estado?"""
        pass

    @abstractmethod
    def can_edit(self):
        """¿Se puede editar en este estado?"""
        pass

    def can_advance(self):
        """¿Puede avanzar al siguiente estado?"""
        return self.next_state() is not None

    def get_name(self):
        """Nombre del estado"""
        return self.__class__.__name__.replace('State', '').replace('Order', '')

    def get_allowed_actions(self):
        """Acciones permitidas en este estado"""
        actions = []
        if self.can_advance():
            actions.append('advance')
        if self.can_cancel():
            actions.append('cancel')
        if self.can_edit():
            actions.append('edit')
        return actions

    def validate_transition(self, order, next_state):
        """Validar si la transición es permitida"""
        return True


class PendingState(OrderState):
    """
    PENDIENTE: Orden recién creada
    Cliente puede editar/cancelar libremente
    """

    def handle(self, order):
        """Marcar como pendiente"""
        print(f"[STATE] Orden #{order.id} → PENDIENTE")
        order.status = 'PENDIENTE'
        order.save()

        # Crear snapshot automático
        from apps.orders.patterns.memento import get_caretaker
        caretaker = get_caretaker()
        caretaker.save(order, tag="pending", reason="Orden creada")

    def next_state(self):
        """Siguiente: En Preparación"""
        return InPreparationState()

    def can_cancel(self):
        return True

    def can_edit(self):
        return True

    def get_name(self):
        return 'PENDIENTE'


class InPreparationState(OrderState):
    """
    EN_PREPARACION: Orden enviada a cocina
    Se puede cancelar pero NO editar
    """

    def handle(self, order):
        """Enviar a cocina"""
        print(f"[STATE] Orden #{order.id} → EN_PREPARACION")
        order.status = 'EN_PREPARACION'
        order.save()

        # Notificar a cocina (Observer)
        from apps.notifications.services import NotificationService
        NotificationService.notify_kitchen(order)

        # Crear snapshot
        from apps.orders.patterns.memento import get_caretaker
        caretaker = get_caretaker()
        caretaker.save(order, tag="in_preparation", reason="Enviada a cocina")

        print(f"[STATE] ✓ Orden #{order.id} enviada a cocina - {order.items.count()} items")

    def next_state(self):
        """Siguiente: Listo"""
        return ReadyState()

    def can_cancel(self):
        return True

    def can_edit(self):
        return False  # NO se puede editar en preparación

    def validate_transition(self, order, next_state):
        """Validar que hay items antes de avanzar"""
        if order.items.count() == 0:
            raise ValueError("La orden no tiene items")
        return True

    def get_name(self):
        return 'EN_PREPARACION'


class ReadyState(OrderState):
    """
    LISTO: Orden preparada, esperando entrega
    NO se puede cancelar ni editar
    """

    def handle(self, order):
        """Marcar como lista"""
        print(f"[STATE] Orden #{order.id} → LISTO")
        order.status = 'LISTO'
        order.prepared_at = datetime.now()
        order.save()

        # Notificar a mesero (Observer)
        from apps.notifications.services import NotificationService
        NotificationService.notify_waiter(order)

        # Crear snapshot
        from apps.orders.patterns.memento import get_caretaker
        caretaker = get_caretaker()
        caretaker.save(order, tag="ready", reason="Orden lista para servir")

        print(f"[STATE] ✓ Orden #{order.id} lista para servir")

    def next_state(self):
        """Siguiente: Entregado"""
        return DeliveredState()

    def can_cancel(self):
        return False  # Ya no se puede cancelar

    def can_edit(self):
        return False

    def get_name(self):
        return 'LISTO'


class DeliveredState(OrderState):
    """
    ENTREGADO: Orden entregada al cliente
    Estado final - NO se puede modificar
    """

    def handle(self, order):
        """Marcar como entregada"""
        print(f"[STATE] Orden #{order.id} → ENTREGADO")
        order.status = 'ENTREGADO'
        order.delivered_at = datetime.now()
        order.save()

        # Snapshot final
        from apps.orders.patterns.memento import get_caretaker
        caretaker = get_caretaker()
        caretaker.save(order, tag="delivered", reason="Orden entregada al cliente")

        print(f"[STATE] ✓ Orden #{order.id} completada exitosamente")

    def next_state(self):
        """Estado final - no hay siguiente"""
        return None

    def can_cancel(self):
        return False

    def can_edit(self):
        return False

    def get_name(self):
        return 'ENTREGADO'


class CancelledState(OrderState):
    """
    CANCELADO: Orden cancelada
    Estado final - NO se puede modificar
    """

    def handle(self, order):
        """Marcar como cancelada"""
        print(f"[STATE] Orden #{order.id} → CANCELADO")
        order.status = 'CANCELADO'
        order.save()

        # Snapshot de cancelación
        from apps.orders.patterns.memento import get_caretaker
        caretaker = get_caretaker()
        caretaker.save(order, tag="cancelled", reason="Orden cancelada")

        print(f"[STATE] ✓ Orden #{order.id} cancelada")

    def next_state(self):
        """Estado final - no hay siguiente"""
        return None

    def can_cancel(self):
        return False

    def can_edit(self):
        return False

    def get_name(self):
        return 'CANCELADO'


class OrderStateManager:
    """
    Gestor centralizado de estados de órdenes
    Coordina transiciones y validaciones
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
        Avanzar orden al siguiente estado con validaciones

        Args:
            order: instancia de Order

        Returns:
            nuevo estado
        """
        current_state = cls.get_state(order)
        next_state = current_state.next_state()

        if next_state is None:
            raise ValueError(f"La orden está en estado final: {order.status}")

        print(f"[STATE MANAGER] Avanzando orden #{order.id}: {current_state.get_name()} → {next_state.get_name()}")

        # Validar transición
        try:
            current_state.validate_transition(order, next_state)
        except ValueError as e:
            print(f"[STATE MANAGER] ✗ Transición inválida: {e}")
            raise

        # Aplicar nuevo estado
        next_state.handle(order)

        print(f"[STATE MANAGER] ✓ Orden #{order.id} avanzada exitosamente")
        return next_state

    @classmethod
    def cancel_order(cls, order, reason=""):
        """Cancelar orden si es posible"""
        current_state = cls.get_state(order)

        if not current_state.can_cancel():
            raise ValueError(f"No se puede cancelar orden en estado {order.status}")

        print(f"[STATE MANAGER] Cancelando orden #{order.id} - Razón: {reason}")

        cancelled_state = CancelledState()
        cancelled_state.handle(order)

        print(f"[STATE MANAGER] ✓ Orden #{order.id} cancelada")
        return cancelled_state

    @classmethod
    def can_advance(cls, order):
        """Verificar si la orden puede avanzar"""
        current_state = cls.get_state(order)
        return current_state.can_advance()

    @classmethod
    def can_cancel(cls, order):
        """Verificar si la orden puede ser cancelada"""
        current_state = cls.get_state(order)
        return current_state.can_cancel()

    @classmethod
    def can_edit(cls, order):
        """Verificar si la orden puede ser editada"""
        current_state = cls.get_state(order)
        return current_state.can_edit()

    @classmethod
    def get_allowed_actions(cls, order):
        """Obtener acciones permitidas para la orden"""
        current_state = cls.get_state(order)
        return current_state.get_allowed_actions()

    @classmethod
    def get_state_info(cls, order):
        """Obtener información completa del estado"""
        current_state = cls.get_state(order)

        return {
            'order_id': order.id,
            'current_state': current_state.get_name(),
            'can_advance': cls.can_advance(order),
            'can_cancel': cls.can_cancel(order),
            'can_edit': cls.can_edit(order),
            'allowed_actions': current_state.get_allowed_actions(),
            'next_state': current_state.next_state().get_name() if current_state.next_state() else None
        }