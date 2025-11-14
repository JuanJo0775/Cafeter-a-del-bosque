"""
Patrón MEMENTO para guardar y restaurar estados de órdenes
Permite rollback y auditoría
"""
from datetime import datetime
import json


class OrderMemento:
    """
    Memento que guarda el estado de una orden en un momento dado
    """

    def __init__(self, order_id, status, total_price, items_snapshot, timestamp=None):
        self._order_id = order_id
        self._status = status
        self._total_price = float(total_price)
        self._items_snapshot = items_snapshot
        self._timestamp = timestamp or datetime.now()

    def get_state(self):
        """Obtener estado guardado"""
        return {
            'order_id': self._order_id,
            'status': self._status,
            'total_price': self._total_price,
            'items': self._items_snapshot,
            'timestamp': self._timestamp.isoformat()
        }

    def get_order_id(self):
        return self._order_id

    def get_status(self):
        return self._status

    def get_timestamp(self):
        return self._timestamp


class OrderOriginator:
    """
    Originator que crea y restaura mementos de órdenes
    """

    def __init__(self, order):
        self._order = order

    def create_memento(self):
        """
        Crear snapshot del estado actual

        Returns:
            OrderMemento con el estado actual
        """
        # Capturar items
        items_snapshot = []
        for item in self._order.items.all():
            items_snapshot.append({
                'product_id': item.product.id,
                'product_name': item.product.name,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'extras': item.extras,
                'subtotal': float(item.subtotal)
            })

        return OrderMemento(
            order_id=self._order.id,
            status=self._order.status,
            total_price=self._order.total_price,
            items_snapshot=items_snapshot
        )

    def restore_from_memento(self, memento: OrderMemento):
        """
        Restaurar orden desde un memento
        NOTA: Solo restaura el estado, no modifica items reales
        """
        state = memento.get_state()

        self._order.status = state['status']
        self._order.total_price = state['total_price']
        self._order.save()

        print(f"[MEMENTO] Orden #{self._order.id} restaurada a estado: {state['status']}")

    def get_state_summary(self):
        """Obtener resumen del estado actual"""
        return {
            'id': self._order.id,
            'status': self._order.status,
            'total': float(self._order.total_price),
            'items_count': self._order.items.count()
        }


class OrderCaretaker:
    """
    Caretaker que mantiene historial de mementos
    """

    def __init__(self):
        self._mementos = {}  # {order_id: [(tag, memento), ...]}

    def save(self, order, tag=""):
        """
        Guardar estado de una orden

        Args:
            order: instancia de Order
            tag: etiqueta opcional para identificar el snapshot
        """
        originator = OrderOriginator(order)
        memento = originator.create_memento()

        if order.id not in self._mementos:
            self._mementos[order.id] = []

        self._mementos[order.id].append((tag or f"snapshot_{len(self._mementos[order.id])}", memento))

        print(f"[MEMENTO] Estado guardado: Orden #{order.id} - {tag}")

    def restore(self, order, tag=""):
        """
        Restaurar orden a un estado guardado

        Args:
            order: instancia de Order
            tag: etiqueta del snapshot a restaurar

        Returns:
            Estado restaurado o None
        """
        if order.id not in self._mementos:
            print(f"[MEMENTO] No hay snapshots para orden #{order.id}")
            return None

        # Buscar memento por tag
        for saved_tag, memento in self._mementos[order.id]:
            if saved_tag == tag:
                originator = OrderOriginator(order)
                originator.restore_from_memento(memento)
                return memento.get_state()

        print(f"[MEMENTO] Tag '{tag}' no encontrado para orden #{order.id}")
        return None

    def get_history(self, order_id):
        """
        Obtener historial de snapshots de una orden

        Args:
            order_id: ID de la orden

        Returns:
            Lista de estados guardados
        """
        if order_id not in self._mementos:
            return []

        history = []
        for tag, memento in self._mementos[order_id]:
            state = memento.get_state()
            state['tag'] = tag
            history.append(state)

        return history

    def get_latest(self, order_id):
        """Obtener el snapshot más reciente"""
        if order_id not in self._mementos or not self._mementos[order_id]:
            return None

        tag, memento = self._mementos[order_id][-1]
        state = memento.get_state()
        state['tag'] = tag
        return state

    def clear_history(self, order_id):
        """Limpiar historial de una orden"""
        if order_id in self._mementos:
            del self._mementos[order_id]
            print(f"[MEMENTO] Historial limpiado para orden #{order_id}")


# Singleton Caretaker global
_caretaker_instance = None


def get_caretaker():
    """Obtener instancia única del Caretaker"""
    global _caretaker_instance
    if _caretaker_instance is None:
        _caretaker_instance = OrderCaretaker()
    return _caretaker_instance