"""
Patrón COMMAND para encapsular acciones sobre órdenes
Permite historial, undo, redo, auditoría
"""
from abc import ABC, abstractmethod
from datetime import datetime
from apps.orders.models import Order, OrderItem, OrderHistory
from apps.menu.models import Product


class Command(ABC):
    """Command abstracto"""

    @abstractmethod
    def execute(self):
        """Ejecutar comando"""
        pass

    @abstractmethod
    def undo(self):
        """Deshacer comando"""
        pass

    @abstractmethod
    def log(self):
        """Registrar en historial"""
        pass


class CreateOrderCommand(Command):
    """Comando para crear una orden"""

    def __init__(self, customer, table_number, items, mesero=None):
        self.customer = customer
        self.table_number = table_number
        self.items = items
        self.mesero = mesero
        self.order = None

    def execute(self):
        """Crear la orden"""
        self.order = Order.objects.create(
            customer=self.customer,
            table_number=self.table_number,
            mesero=self.mesero
        )

        # Agregar items
        for item_data in self.items:
            product = Product.objects.get(id=item_data['product_id'])
            item = OrderItem(
                order=self.order,
                product=product,
                quantity=item_data.get('quantity', 1),
                extras=item_data.get('extras', {})
            )
            item.calculate_subtotal()
            item.save()

        self.order.calculate_total()
        self.log()

        return self.order

    def undo(self):
        """Eliminar la orden creada"""
        if self.order:
            self.order.delete()
            self.order = None

    def log(self):
        """Registrar en historial"""
        if self.order:
            OrderHistory.objects.create(
                order=self.order,
                action='CREATE',
                new_status=self.order.status,
                changed_by=self.customer
            )


class UpdateOrderStatusCommand(Command):
    """Comando para actualizar estado de orden"""

    def __init__(self, order, new_status, user=None):
        self.order = order
        self.new_status = new_status
        self.previous_status = order.status
        self.user = user

    def execute(self):
        """Cambiar estado"""
        self.order.status = self.new_status

        # Actualizar timestamps según el estado
        if self.new_status == 'LISTO':
            self.order.prepared_at = datetime.now()
        elif self.new_status == 'ENTREGADO':
            self.order.delivered_at = datetime.now()

        self.order.save()
        self.log()

        return self.order

    def undo(self):
        """Revertir al estado anterior"""
        self.order.status = self.previous_status
        self.order.save()

    def log(self):
        """Registrar cambio"""
        OrderHistory.objects.create(
            order=self.order,
            action='STATUS_CHANGE',
            previous_status=self.previous_status,
            new_status=self.new_status,
            changed_by=self.user
        )


class CancelOrderCommand(Command):
    """Comando para cancelar orden"""

    def __init__(self, order, reason="", user=None):
        self.order = order
        self.reason = reason
        self.user = user
        self.previous_status = order.status

    def execute(self):
        """Cancelar orden"""
        if not self.order.can_cancel():
            raise ValueError(f"No se puede cancelar orden en estado {self.order.status}")

        self.order.status = 'CANCELADO'
        self.order.save()
        self.log()

        return self.order

    def undo(self):
        """Restaurar orden"""
        self.order.status = self.previous_status
        self.order.save()

    def log(self):
        """Registrar cancelación"""
        OrderHistory.objects.create(
            order=self.order,
            action='CANCEL',
            previous_status=self.previous_status,
            new_status='CANCELADO',
            changed_by=self.user,
            reason=self.reason
        )


class AddItemCommand(Command):
    """Comando para agregar item a orden existente"""

    def __init__(self, order, product_id, quantity=1, extras=None):
        self.order = order
        self.product_id = product_id
        self.quantity = quantity
        self.extras = extras or {}
        self.item = None

    def execute(self):
        """Agregar item"""
        product = Product.objects.get(id=self.product_id)

        self.item = OrderItem(
            order=self.order,
            product=product,
            quantity=self.quantity,
            extras=self.extras
        )
        self.item.calculate_subtotal()
        self.item.save()

        self.order.calculate_total()
        self.log()

        return self.item

    def undo(self):
        """Eliminar item agregado"""
        if self.item:
            self.item.delete()
            self.order.calculate_total()

    def log(self):
        """Registrar adición"""
        OrderHistory.objects.create(
            order=self.order,
            action='ADD_ITEM',
            reason=f"Agregado: {self.item.product.name} x{self.quantity}"
        )


class CommandInvoker:
    """
    Invoker que ejecuta comandos y mantiene historial
    """

    def __init__(self):
        self._history = []
        self._current = -1

    def execute_command(self, command: Command):
        """Ejecutar comando y guardarlo en historial"""
        result = command.execute()

        # Limpiar historial futuro si estamos en medio
        self._history = self._history[:self._current + 1]

        # Agregar comando
        self._history.append(command)
        self._current += 1

        return result

    def undo(self):
        """Deshacer último comando"""
        if self._current >= 0:
            command = self._history[self._current]
            command.undo()
            self._current -= 1
            return True
        return False

    def redo(self):
        """Rehacer comando"""
        if self._current < len(self._history) - 1:
            self._current += 1
            command = self._history[self._current]
            command.execute()
            return True
        return False

    def get_history(self):
        """Obtener historial de comandos"""
        return self._history[:self._current + 1]