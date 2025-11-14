"""
COMMAND: Encapsular acciones sobre órdenes con historial y undo/redo
"""
from abc import ABC, abstractmethod
from datetime import datetime
from apps.orders.models import Order, OrderItem, OrderHistory
from apps.menu.models import Product
from apps.menu.decorators.product_decorator import DecoratorFactory
from decimal import Decimal


class Command(ABC):
    """Command abstracto con soporte para undo/redo"""

    def __init__(self):
        self.executed_at = None
        self.undone_at = None

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

    def can_undo(self):
        """Verificar si se puede deshacer"""
        return self.executed_at is not None and self.undone_at is None

    @abstractmethod
    def get_description(self):
        """Descripción del comando"""
        pass


class CreateOrderCommand(Command):
    """Comando para crear una orden completa"""

    def __init__(self, customer, table_number, items, mesero=None, instructions=""):
        super().__init__()
        self.customer = customer
        self.table_number = table_number
        self.items = items
        self.mesero = mesero
        self.instructions = instructions
        self.order = None

    def execute(self):
        """Crear la orden con todos sus items"""
        print(f"[COMMAND] Ejecutando CreateOrderCommand...")

        self.order = Order.objects.create(
            customer=self.customer,
            table_number=self.table_number,
            mesero=self.mesero,
            special_instructions=self.instructions,
            status='PENDIENTE'
        )

        # Agregar items con decoradores
        for item_data in self.items:
            product = Product.objects.get(id=item_data['product_id'])
            extras = item_data.get('extras', {})

            # Calcular precio con decoradores
            decorated_info = DecoratorFactory.get_decorated_info(product, extras)

            item = OrderItem.objects.create(
                order=self.order,
                product=product,
                quantity=item_data.get('quantity', 1),
                unit_price=Decimal(str(decorated_info['price'])),
                extras=extras
            )
            item.calculate_subtotal()

        self.order.calculate_total()
        self.executed_at = datetime.now()
        self.log()

        print(f"[COMMAND] ✓ Orden #{self.order.id} creada - Total: ${self.order.total_price}")
        return self.order

    def undo(self):
        """Eliminar la orden creada"""
        if not self.can_undo():
            raise Exception("No se puede deshacer este comando")

        print(f"[COMMAND] Deshaciendo CreateOrderCommand - Orden #{self.order.id}")

        order_id = self.order.id
        self.order.delete()
        self.order = None
        self.undone_at = datetime.now()

        print(f"[COMMAND] ✓ Orden #{order_id} eliminada")

    def log(self):
        """Registrar creación en historial"""
        if self.order:
            OrderHistory.objects.create(
                order=self.order,
                action='CREATE',
                new_status=self.order.status,
                changed_by=self.customer,
                reason=f"Orden creada - Mesa {self.table_number}"
            )

    def get_description(self):
        return f"Crear orden - Mesa {self.table_number} - {len(self.items)} items"


class UpdateOrderStatusCommand(Command):
    """Comando para actualizar estado de orden"""

    def __init__(self, order, new_status, user=None, reason=""):
        super().__init__()
        self.order = order
        self.new_status = new_status
        self.previous_status = order.status
        self.user = user
        self.reason = reason

    def execute(self):
        """Cambiar estado de la orden"""
        print(f"[COMMAND] Cambiando estado: {self.previous_status} -> {self.new_status}")

        self.order.status = self.new_status

        # Actualizar timestamps según estado
        if self.new_status == 'EN_PREPARACION':
            print(f"[COMMAND] Orden #{self.order.id} enviada a cocina")
        elif self.new_status == 'LISTO':
            self.order.prepared_at = datetime.now()
            print(f"[COMMAND] Orden #{self.order.id} lista para servir")
        elif self.new_status == 'ENTREGADO':
            self.order.delivered_at = datetime.now()
            print(f"[COMMAND] Orden #{self.order.id} entregada al cliente")

        self.order.save()
        self.executed_at = datetime.now()
        self.log()

        return self.order

    def undo(self):
        """Revertir al estado anterior"""
        if not self.can_undo():
            raise Exception("No se puede deshacer este comando")

        print(f"[COMMAND] Revirtiendo estado: {self.new_status} -> {self.previous_status}")

        self.order.status = self.previous_status

        # Limpiar timestamps si es necesario
        if self.previous_status == 'PENDIENTE':
            self.order.prepared_at = None
            self.order.delivered_at = None
        elif self.previous_status == 'EN_PREPARACION':
            self.order.prepared_at = None
            self.order.delivered_at = None
        elif self.previous_status == 'LISTO':
            self.order.delivered_at = None

        self.order.save()
        self.undone_at = datetime.now()

        print(f"[COMMAND] ✓ Estado revertido")

    def log(self):
        """Registrar cambio de estado"""
        OrderHistory.objects.create(
            order=self.order,
            action='STATUS_CHANGE',
            previous_status=self.previous_status,
            new_status=self.new_status,
            changed_by=self.user,
            reason=self.reason
        )

    def get_description(self):
        return f"Cambiar estado: {self.previous_status} -> {self.new_status}"


class CancelOrderCommand(Command):
    """Comando para cancelar orden"""

    def __init__(self, order, reason="", user=None):
        super().__init__()
        self.order = order
        self.reason = reason
        self.user = user
        self.previous_status = order.status
        self.previous_data = None

    def execute(self):
        """Cancelar orden si es posible"""
        if not self.order.can_cancel():
            raise ValueError(f"No se puede cancelar orden en estado {self.order.status}")

        print(f"[COMMAND] Cancelando orden #{self.order.id}")

        # Guardar datos antes de cancelar
        self.previous_data = {
            'status': self.order.status,
            'prepared_at': self.order.prepared_at,
            'delivered_at': self.order.delivered_at
        }

        self.order.status = 'CANCELADO'
        self.order.save()
        self.executed_at = datetime.now()
        self.log()

        print(f"[COMMAND] ✓ Orden #{self.order.id} cancelada - Razón: {self.reason}")
        return self.order

    def undo(self):
        """Restaurar orden cancelada"""
        if not self.can_undo():
            raise Exception("No se puede deshacer este comando")

        print(f"[COMMAND] Restaurando orden cancelada #{self.order.id}")

        if self.previous_data:
            self.order.status = self.previous_data['status']
            self.order.prepared_at = self.previous_data['prepared_at']
            self.order.delivered_at = self.previous_data['delivered_at']
            self.order.save()

        self.undone_at = datetime.now()

        print(f"[COMMAND] ✓ Orden #{self.order.id} restaurada")

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

    def get_description(self):
        return f"Cancelar orden #{self.order.id} - Razón: {self.reason}"


class AddItemCommand(Command):
    """Comando para agregar item a orden existente"""

    def __init__(self, order, product_id, quantity=1, extras=None):
        super().__init__()
        self.order = order
        self.product_id = product_id
        self.quantity = quantity
        self.extras = extras or {}
        self.item = None

    def execute(self):
        """Agregar item a la orden"""
        if self.order.status not in ['PENDIENTE']:
            raise ValueError(f"No se pueden agregar items a orden en estado {self.order.status}")

        print(f"[COMMAND] Agregando item a orden #{self.order.id}")

        product = Product.objects.get(id=self.product_id)

        # Calcular precio con decoradores
        decorated_info = DecoratorFactory.get_decorated_info(product, self.extras)

        self.item = OrderItem.objects.create(
            order=self.order,
            product=product,
            quantity=self.quantity,
            unit_price=Decimal(str(decorated_info['price'])),
            extras=self.extras
        )
        self.item.calculate_subtotal()

        self.order.calculate_total()
        self.executed_at = datetime.now()
        self.log()

        print(f"[COMMAND] ✓ Item agregado: {decorated_info['name']} x{self.quantity}")
        return self.item

    def undo(self):
        """Eliminar item agregado"""
        if not self.can_undo():
            raise Exception("No se puede deshacer este comando")

        print(f"[COMMAND] Eliminando item de orden #{self.order.id}")

        if self.item:
            self.item.delete()
            self.order.calculate_total()
            self.item = None

        self.undone_at = datetime.now()

        print("[COMMAND] ✓ Item eliminado")

    def log(self):
        """Registrar adición de item"""
        OrderHistory.objects.create(
            order=self.order,
            action='ADD_ITEM',
            changed_by=None,
            reason=f"Item agregado: {self.item.product.name} x{self.quantity}"
        )

    def get_description(self):
        product_name = Product.objects.get(id=self.product_id).name
        return f"Agregar item: {product_name} x{self.quantity}"


class RemoveItemCommand(Command):
    """Comando para remover item de orden"""

    def __init__(self, order, item_id):
        super().__init__()
        self.order = order
        self.item_id = item_id
        self.item_data = None

    def execute(self):
        """Remover item de la orden"""
        if self.order.status not in ['PENDIENTE']:
            raise ValueError(f"No se pueden remover items de orden en estado {self.order.status}")

        print(f"[COMMAND] Removiendo item {self.item_id} de orden #{self.order.id}")

        item = OrderItem.objects.get(id=self.item_id, order=self.order)

        # Guardar datos para undo
        self.item_data = {
            'product_id': item.product.id,
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'extras': item.extras,
            'product_name': item.product.name
        }

        item.delete()
        self.order.calculate_total()
        self.executed_at = datetime.now()
        self.log()

        print(f"[COMMAND] ✓ Item removido: {self.item_data['product_name']}")
        return self.order

    def undo(self):
        """Restaurar item removido"""
        if not self.can_undo():
            raise Exception("No se puede deshacer este comando")

        print(f"[COMMAND] Restaurando item en orden #{self.order.id}")

        if self.item_data:
            product = Product.objects.get(id=self.item_data['product_id'])

            OrderItem.objects.create(
                order=self.order,
                product=product,
                quantity=self.item_data['quantity'],
                unit_price=self.item_data['unit_price'],
                extras=self.item_data['extras']
            )

            self.order.calculate_total()

        self.undone_at = datetime.now()

        print("[COMMAND] ✓ Item restaurado")

    def log(self):
        """Registrar eliminación"""
        if self.item_data:
            OrderHistory.objects.create(
                order=self.order,
                action='REMOVE_ITEM',
                reason=f"Item removido: {self.item_data['product_name']}"
            )

    def get_description(self):
        return f"Remover item #{self.item_id}"


class UpdateItemQuantityCommand(Command):
    """Comando para actualizar cantidad de un item"""

    def __init__(self, order, item_id, new_quantity):
        super().__init__()
        self.order = order
        self.item_id = item_id
        self.new_quantity = new_quantity
        self.previous_quantity = None
        self.item = None

    def execute(self):
        """Actualizar cantidad del item"""
        if self.order.status not in ['PENDIENTE']:
            raise ValueError(f"No se puede editar orden en estado {self.order.status}")

        print(f"[COMMAND] Actualizando cantidad de item {self.item_id}")

        self.item = OrderItem.objects.get(id=self.item_id, order=self.order)
        self.previous_quantity = self.item.quantity

        self.item.quantity = self.new_quantity
        self.item.calculate_subtotal()

        self.order.calculate_total()
        self.executed_at = datetime.now()
        self.log()

        print(f"[COMMAND] ✓ Cantidad actualizada: {self.previous_quantity} -> {self.new_quantity}")
        return self.item

    def undo(self):
        """Revertir cantidad"""
        if not self.can_undo():
            raise Exception("No se puede deshacer este comando")

        print(f"[COMMAND] Revirtiendo cantidad: {self.new_quantity} -> {self.previous_quantity}")

        if self.item:
            self.item.quantity = self.previous_quantity
            self.item.calculate_subtotal()
            self.order.calculate_total()

        self.undone_at = datetime.now()

        print("[COMMAND] ✓ Cantidad revertida")

    def log(self):
        """Registrar actualización"""
        if self.item:
            OrderHistory.objects.create(
                order=self.order,
                action='UPDATE_QUANTITY',
                reason=f"Cantidad actualizada: {self.item.product.name} - {self.previous_quantity} -> {self.new_quantity}"
            )

    def get_description(self):
        return f"Actualizar cantidad item #{self.item_id}: {self.previous_quantity} -> {self.new_quantity}"


class CommandInvoker:
    """
    Invoker que ejecuta comandos y mantiene historial completo
    Soporta undo/redo con límite de historia
    """

    def __init__(self, max_history=50):
        self._history = []
        self._current = -1
        self.max_history = max_history

    def execute_command(self, command: Command):
        """
        Ejecutar comando y agregarlo al historial

        Args:
            command: Command a ejecutar

        Returns:
            resultado del comando
        """
        print(f"[INVOKER] Ejecutando: {command.get_description()}")

        result = command.execute()

        # Limpiar historial futuro si estamos en medio
        self._history = self._history[:self._current + 1]

        # Agregar comando
        self._history.append(command)
        self._current += 1

        # Limitar tamaño del historial
        if len(self._history) > self.max_history:
            removed = self._history.pop(0)
            self._current -= 1
            print(f"[INVOKER] Comando antiguo removido del historial")

        print(f"[INVOKER] ✓ Comando ejecutado - Posición en historial: {self._current + 1}/{len(self._history)}")
        return result

    def undo(self):
        """Deshacer último comando"""
        if self._current >= 0:
            command = self._history[self._current]

            if not command.can_undo():
                print(f"[INVOKER] ✗ No se puede deshacer: {command.get_description()}")
                return False

            print(f"[INVOKER] Deshaciendo: {command.get_description()}")
            command.undo()
            self._current -= 1

            print(f"[INVOKER] ✓ Comando deshecho - Posición: {self._current + 1}/{len(self._history)}")
            return True

        print("[INVOKER] ✗ No hay comandos para deshacer")
        return False

    def redo(self):
        """Rehacer comando"""
        if self._current < len(self._history) - 1:
            self._current += 1
            command = self._history[self._current]

            print(f"[INVOKER] Rehaciendo: {command.get_description()}")
            command.execute()

            print(f"[INVOKER] ✓ Comando rehecho - Posición: {self._current + 1}/{len(self._history)}")
            return True

        print("[INVOKER] ✗ No hay comandos para rehacer")
        return False

    def get_history(self):
        """Obtener historial de comandos ejecutados"""
        return [
            {
                'description': cmd.get_description(),
                'executed_at': cmd.executed_at.isoformat() if cmd.executed_at else None,
                'undone_at': cmd.undone_at.isoformat() if cmd.undone_at else None,
                'can_undo': cmd.can_undo()
            }
            for cmd in self._history[:self._current + 1]
        ]

    def get_undo_stack(self):
        """Obtener comandos que pueden deshacerse"""
        return [
            cmd.get_description()
            for cmd in self._history[:self._current + 1]
            if cmd.can_undo()
        ]

    def get_redo_stack(self):
        """Obtener comandos que pueden rehacerse"""
        return [
            cmd.get_description()
            for cmd in self._history[self._current + 1:]
        ]

    def clear_history(self):
        """Limpiar historial completo"""
        self._history = []
        self._current = -1
        print("[INVOKER] Historial limpiado")

    def get_stats(self):
        """Obtener estadísticas del invoker"""
        return {
            'total_commands': len(self._history),
            'current_position': self._current + 1,
            'can_undo': self._current >= 0,
            'can_redo': self._current < len(self._history) - 1,
            'undo_available': len(self.get_undo_stack()),
            'redo_available': len(self.get_redo_stack())
        }