"""
MEMENTO: Guardar y restaurar estados completos de órdenes
Sistema de snapshots con compresión y gestión de memoria
"""
from datetime import datetime
import json
from decimal import Decimal


class OrderMemento:
    """
    Memento que almacena un snapshot completo de una orden
    Inmutable después de creación
    """

    def __init__(self, order_id, status, total_price, items_snapshot, metadata=None):
        self._order_id = order_id
        self._status = status
        self._total_price = float(total_price)
        self._items_snapshot = items_snapshot
        self._metadata = metadata or {}
        self._timestamp = datetime.now()
        self._checksum = self._calculate_checksum()

    def _calculate_checksum(self):
        """Calcular checksum simple para validación"""
        data = f"{self._order_id}{self._status}{self._total_price}{len(self._items_snapshot)}"
        return hash(data)

    def get_state(self):
        """Obtener estado completo del memento"""
        return {
            'order_id': self._order_id,
            'status': self._status,
            'total_price': self._total_price,
            'items': self._items_snapshot,
            'metadata': self._metadata,
            'timestamp': self._timestamp.isoformat(),
            'checksum': self._checksum
        }

    def get_order_id(self):
        return self._order_id

    def get_status(self):
        return self._status

    def get_timestamp(self):
        return self._timestamp

    def get_total_price(self):
        return self._total_price

    def get_items_count(self):
        return len(self._items_snapshot)

    def is_valid(self):
        """Verificar integridad del memento"""
        expected_checksum = hash(
            f"{self._order_id}{self._status}{self._total_price}{len(self._items_snapshot)}"
        )
        return self._checksum == expected_checksum

    def get_summary(self):
        """Resumen compacto del memento"""
        return {
            'timestamp': self._timestamp.isoformat(),
            'status': self._status,
            'total': self._total_price,
            'items_count': len(self._items_snapshot),
            'valid': self.is_valid()
        }


class OrderOriginator:
    """
    Originator que crea y restaura mementos de órdenes
    """

    def __init__(self, order):
        self._order = order

    def create_memento(self, tag="", reason=""):
        """
        Crear snapshot del estado actual

        Args:
            tag: etiqueta opcional
            reason: razón del snapshot

        Returns:
            OrderMemento con estado actual
        """
        print(f"[MEMENTO] Creando snapshot de orden #{self._order.id}")

        # Capturar estado completo de items
        items_snapshot = []
        for item in self._order.items.all():
            items_snapshot.append({
                'product_id': item.product.id,
                'product_name': item.product.name,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'extras': item.extras,
                'extras_price': float(item.extras_price),
                'subtotal': float(item.subtotal)
            })

        # Metadata adicional
        metadata = {
            'tag': tag,
            'reason': reason,
            'customer_id': self._order.customer.id,
            'customer_name': self._order.customer.username,
            'mesero_id': self._order.mesero.id if self._order.mesero else None,
            'mesero_name': self._order.mesero.username if self._order.mesero else None,
            'table_number': self._order.table_number,
            'special_instructions': self._order.special_instructions,
            'created_at': self._order.created_at.isoformat(),
            'prepared_at': self._order.prepared_at.isoformat() if self._order.prepared_at else None,
            'delivered_at': self._order.delivered_at.isoformat() if self._order.delivered_at else None
        }

        memento = OrderMemento(
            order_id=self._order.id,
            status=self._order.status,
            total_price=self._order.total_price,
            items_snapshot=items_snapshot,
            metadata=metadata
        )

        print(f"[MEMENTO] ✓ Snapshot creado - Items: {len(items_snapshot)}, Total: ${self._order.total_price}")
        return memento

    def restore_from_memento(self, memento: OrderMemento):
        """
        Restaurar orden desde un memento

        Args:
            memento: OrderMemento a restaurar
        """
        if not memento.is_valid():
            raise ValueError("Memento corrupto - checksum inválido")

        print(f"[MEMENTO] Restaurando orden #{self._order.id} desde snapshot")

        state = memento.get_state()

        # Restaurar estado básico
        self._order.status = state['status']
        self._order.total_price = Decimal(str(state['total_price']))

        # Restaurar metadata
        metadata = state['metadata']
        self._order.table_number = metadata.get('table_number', self._order.table_number)
        self._order.special_instructions = metadata.get('special_instructions', '')

        self._order.save()

        print(f"[MEMENTO] ✓ Orden restaurada - Estado: {state['status']}, Total: ${state['total_price']}")

    def get_state_summary(self):
        """Resumen del estado actual"""
        return {
            'id': self._order.id,
            'status': self._order.status,
            'total': float(self._order.total_price),
            'items_count': self._order.items.count(),
            'table': self._order.table_number,
            'customer': self._order.customer.username
        }

    def compare_with_memento(self, memento: OrderMemento):
        """
        Comparar estado actual con memento

        Returns:
            dict con diferencias
        """
        current_state = self.get_state_summary()
        memento_state = memento.get_state()

        differences = {}

        if current_state['status'] != memento_state['status']:
            differences['status'] = {
                'current': current_state['status'],
                'memento': memento_state['status']
            }

        if current_state['total'] != memento_state['total_price']:
            differences['total'] = {
                'current': current_state['total'],
                'memento': memento_state['total_price']
            }

        if current_state['items_count'] != len(memento_state['items']):
            differences['items_count'] = {
                'current': current_state['items_count'],
                'memento': len(memento_state['items'])
            }

        return differences


class OrderCaretaker:
    """
    Caretaker que gestiona colección de mementos
    Implementa límites de memoria y limpieza automática
    """

    def __init__(self, max_snapshots_per_order=10):
        self._mementos = {}  # {order_id: [(tag, memento), ...]}
        self.max_snapshots_per_order = max_snapshots_per_order

    def save(self, order, tag="", reason=""):
        """
        Guardar snapshot de una orden

        Args:
            order: instancia de Order
            tag: etiqueta identificadora
            reason: razón del snapshot
        """
        originator = OrderOriginator(order)
        memento = originator.create_memento(tag=tag, reason=reason)

        if order.id not in self._mementos:
            self._mementos[order.id] = []

        # Agregar memento
        self._mementos[order.id].append((tag or f"snapshot_{len(self._mementos[order.id])}", memento))

        # Limitar cantidad de snapshots
        if len(self._mementos[order.id]) > self.max_snapshots_per_order:
            removed_tag, removed_memento = self._mementos[order.id].pop(0)
            print(f"[CARETAKER] Snapshot antiguo removido: {removed_tag}")

        print(f"[CARETAKER] Snapshot guardado - Orden #{order.id}, Tag: {tag}, Total snapshots: {len(self._mementos[order.id])}")

    def restore(self, order, tag=""):
        """
        Restaurar orden desde snapshot

        Args:
            order: instancia de Order
            tag: etiqueta del snapshot a restaurar

        Returns:
            dict con estado restaurado o None
        """
        if order.id not in self._mementos:
            print(f"[CARETAKER] No hay snapshots para orden #{order.id}")
            return None

        # Buscar memento por tag
        for saved_tag, memento in self._mementos[order.id]:
            if saved_tag == tag:
                originator = OrderOriginator(order)
                originator.restore_from_memento(memento)
                return memento.get_state()

        print(f"[CARETAKER] Tag '{tag}' no encontrado para orden #{order.id}")
        return None

    def get_history(self, order_id):
        """
        Obtener historial completo de snapshots

        Args:
            order_id: ID de la orden

        Returns:
            lista de estados guardados
        """
        if order_id not in self._mementos:
            return []

        history = []
        for tag, memento in self._mementos[order_id]:
            summary = memento.get_summary()
            summary['tag'] = tag
            summary['metadata'] = memento.get_state()['metadata']
            history.append(summary)

        return history

    def get_latest(self, order_id):
        """Obtener snapshot más reciente"""
        if order_id not in self._mementos or not self._mementos[order_id]:
            return None

        tag, memento = self._mementos[order_id][-1]
        state = memento.get_state()
        state['tag'] = tag
        return state

    def get_by_tag(self, order_id, tag):
        """Obtener snapshot específico por tag"""
        if order_id not in self._mementos:
            return None

        for saved_tag, memento in self._mementos[order_id]:
            if saved_tag == tag:
                state = memento.get_state()
                state['tag'] = saved_tag
                return state

        return None

    def clear_history(self, order_id):
        """Limpiar historial de una orden"""
        if order_id in self._mementos:
            count = len(self._mementos[order_id])
            del self._mementos[order_id]
            print(f"[CARETAKER] Historial limpiado para orden #{order_id} - {count} snapshots removidos")

    def clear_old_snapshots(self, days=7):
        """
        Limpiar snapshots antiguos

        Args:
            days: días de antigüedad para eliminar
        """
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)

        removed_count = 0
        for order_id, snapshots in list(self._mementos.items()):
            filtered = [
                (tag, memento)
                for tag, memento in snapshots
                if memento.get_timestamp() > cutoff_date
            ]

            removed = len(snapshots) - len(filtered)
            removed_count += removed

            if filtered:
                self._mementos[order_id] = filtered
            else:
                del self._mementos[order_id]

        print(f"[CARETAKER] Limpieza completada - {removed_count} snapshots antiguos removidos")

    def get_stats(self):
        """Obtener estadísticas del caretaker"""
        total_snapshots = sum(len(snapshots) for snapshots in self._mementos.values())

        return {
            'total_orders': len(self._mementos),
            'total_snapshots': total_snapshots,
            'max_per_order': self.max_snapshots_per_order,
            'orders_with_snapshots': list(self._mementos.keys())
        }

    def export_history(self, order_id):
        """
        Exportar historial en formato JSON

        Returns:
            str JSON con historial completo
        """
        history = self.get_history(order_id)
        return json.dumps(history, indent=2, default=str)


# Singleton global del Caretaker
_caretaker_instance = None


def get_caretaker():
    """Obtener instancia única del Caretaker"""
    global _caretaker_instance
    if _caretaker_instance is None:
        _caretaker_instance = OrderCaretaker()
    return _caretaker_instance