"""
TEMPLATE METHOD: Plantillas base para procesos de órdenes
Define estructura general, subclases implementan pasos específicos
"""
from abc import ABC, abstractmethod


class OrderProcessTemplate(ABC):
    """
    Plantilla abstracta para procesar órdenes
    Define el esqueleto del algoritmo
    """

    def process_order(self, order):
        """
        Método template - define la secuencia de pasos

        Args:
            order: instancia de Order

        Returns:
            dict con resultado del proceso
        """
        print(f"\n[TEMPLATE] === Iniciando proceso de orden #{order.id} ===")

        # 1. Validar orden
        if not self.validate_order(order):
            return {
                'success': False,
                'error': 'Validación fallida',
                'order_id': order.id
            }

        # 2. Preparar orden
        preparation_result = self.prepare_order(order)
        if not preparation_result:
            return {
                'success': False,
                'error': 'Preparación fallida',
                'order_id': order.id
            }

        # 3. Procesar items (paso específico)
        items_result = self.process_items(order)

        # 4. Calcular totales
        self.calculate_totals(order)

        # 5. Notificar (opcional - hook)
        if self.should_notify():
            self.notify_stakeholders(order)

        # 6. Guardar estado
        self.save_state(order)

        # 7. Post-procesamiento (hook opcional)
        self.post_process(order)

        print(f"[TEMPLATE] === Proceso completado para orden #{order.id} ===\n")

        return {
            'success': True,
            'order_id': order.id,
            'status': order.status,
            'total': float(order.total_price),
            'items_processed': items_result
        }

    # Métodos abstractos (deben implementarse)

    @abstractmethod
    def validate_order(self, order):
        """Validar orden antes de procesar"""
        pass

    @abstractmethod
    def process_items(self, order):
        """Procesar items de la orden"""
        pass

    # Métodos concretos (implementación por defecto)

    def prepare_order(self, order):
        """Preparar orden para procesamiento"""
        print(f"[TEMPLATE] Preparando orden #{order.id}")
        return True

    def calculate_totals(self, order):
        """Calcular totales de la orden"""
        print(f"[TEMPLATE] Calculando totales orden #{order.id}")
        order.calculate_total()

    def save_state(self, order):
        """Guardar estado de la orden"""
        print(f"[TEMPLATE] Guardando estado orden #{order.id}")

        # Guardar memento automáticamente
        from apps.orders.patterns.memento import get_caretaker
        caretaker = get_caretaker()
        caretaker.save(order, tag=f"process_{order.status}", reason="Procesamiento automático")

    # Hooks (métodos opcionales con implementación vacía)

    def should_notify(self):
        """Hook: determinar si se debe notificar"""
        return True

    def notify_stakeholders(self, order):
        """Hook: notificar a interesados"""
        print(f"[TEMPLATE] Notificando stakeholders para orden #{order.id}")

    def post_process(self, order):
        """Hook: post-procesamiento opcional"""
        pass


class NewOrderProcessTemplate(OrderProcessTemplate):
    """
    Template para procesar órdenes nuevas
    """

    def validate_order(self, order):
        """Validar nueva orden"""
        print(f"[NEW ORDER] Validando nueva orden #{order.id}")

        # Validar que tenga items
        if order.items.count() == 0:
            print("[NEW ORDER] ✗ Orden sin items")
            return False

        # Validar que tenga cliente
        if not order.customer:
            print("[NEW ORDER] ✗ Orden sin cliente")
            return False

        # Validar que esté en estado correcto
        if order.status != 'PENDIENTE':
            print(f"[NEW ORDER] ✗ Estado incorrecto: {order.status}")
            return False

        print("[NEW ORDER] ✓ Validación exitosa")
        return True

    def process_items(self, order):
        """Procesar items de nueva orden"""
        print(f"[NEW ORDER] Procesando {order.items.count()} items")

        processed = []
        for item in order.items.all():
            # Verificar disponibilidad
            if not item.product.is_available:
                print(f"[NEW ORDER] ⚠️ Producto no disponible: {item.product.name}")
                continue

            # Calcular subtotal
            item.calculate_subtotal()

            processed.append({
                'product': item.product.name,
                'quantity': item.quantity,
                'subtotal': float(item.subtotal)
            })

            print(f"[NEW ORDER] ✓ {item.product.name} x{item.quantity}")

        return processed

    def notify_stakeholders(self, order):
        """Notificar cocina de nueva orden"""
        print(f"[NEW ORDER] Notificando cocina sobre orden #{order.id}")

        from apps.notifications.services import NotificationService
        NotificationService.notify_new_order(order)

    def post_process(self, order):
        """Enrutar a cocina automáticamente"""
        print(f"[NEW ORDER] Enrutando a cocina")

        from apps.kitchen.handlers import KitchenRouter
        router = KitchenRouter()
        router.route_order(order)


class ReadyOrderProcessTemplate(OrderProcessTemplate):
    """
    Template para procesar órdenes listas
    """

    def validate_order(self, order):
        """Validar orden lista"""
        print(f"[READY ORDER] Validando orden lista #{order.id}")

        # Debe estar en preparación
        if order.status != 'EN_PREPARACION':
            print(f"[READY ORDER] ✗ Estado incorrecto: {order.status}")
            return False

        print("[READY ORDER] ✓ Validación exitosa")
        return True

    def process_items(self, order):
        """Verificar que todos los items estén completos"""
        print(f"[READY ORDER] Verificando items completos")

        from apps.kitchen.models import StationQueue

        # Verificar que todas las estaciones completaron
        pending = StationQueue.objects.filter(
            order=order,
            is_completed=False
        ).count()

        if pending > 0:
            print(f"[READY ORDER] ⚠️ {pending} estaciones pendientes")
            return []

        print("[READY ORDER] ✓ Todos los items completos")
        return [{'status': 'all_complete'}]

    def notify_stakeholders(self, order):
        """Notificar mesero que orden está lista"""
        print(f"[READY ORDER] Notificando mesero")

        from apps.notifications.services import NotificationService
        NotificationService.notify_order_ready(order)


class DeliveredOrderProcessTemplate(OrderProcessTemplate):
    """
    Template para procesar órdenes entregadas
    """

    def validate_order(self, order):
        """Validar orden para entrega"""
        print(f"[DELIVERED ORDER] Validando orden #{order.id}")

        # Debe estar lista
        if order.status != 'LISTO':
            print(f"[DELIVERED ORDER] ✗ Estado incorrecto: {order.status}")
            return False

        print("[DELIVERED ORDER] ✓ Validación exitosa")
        return True

    def process_items(self, order):
        """Marcar items como entregados"""
        print(f"[DELIVERED ORDER] Marcando items como entregados")

        return [{
            'status': 'delivered',
            'items_count': order.items.count()
        }]

    def notify_stakeholders(self, order):
        """Notificar cliente que orden fue entregada"""
        print(f"[DELIVERED ORDER] Notificando cliente")

        from apps.notifications.services import NotificationService
        NotificationService.notify_order_delivered(order)

    def post_process(self, order):
        """Limpiar recursos y actualizar estadísticas"""
        print(f"[DELIVERED ORDER] Post-procesamiento")

        # Aquí se podría actualizar estadísticas, limpiar colas, etc.
        from apps.kitchen.models import StationQueue

        # Marcar como completadas las colas
        StationQueue.objects.filter(order=order).update(is_completed=True)


class CancelledOrderProcessTemplate(OrderProcessTemplate):
    """
    Template para procesar órdenes canceladas
    """

    def validate_order(self, order):
        """Validar que se pueda cancelar"""
        print(f"[CANCELLED ORDER] Validando cancelación #{order.id}")

        if not order.can_cancel():
            print(f"[CANCELLED ORDER] ✗ No se puede cancelar en estado {order.status}")
            return False

        print("[CANCELLED ORDER] ✓ Se puede cancelar")
        return True

    def process_items(self, order):
        """Liberar items de las colas"""
        print(f"[CANCELLED ORDER] Liberando items de colas")

        from apps.kitchen.models import StationQueue

        # Remover de colas de cocina
        queues = StationQueue.objects.filter(order=order, is_completed=False)
        count = queues.count()
        queues.delete()

        print(f"[CANCELLED ORDER] ✓ {count} items liberados de colas")

        return [{'released_items': count}]

    def notify_stakeholders(self, order):
        """Notificar cancelación"""
        print(f"[CANCELLED ORDER] Notificando cancelación")

        from apps.notifications.services import NotificationService
        NotificationService.notify_order_cancelled(order, reason="Orden cancelada")

    def post_process(self, order):
        """Registrar cancelación en historial"""
        print(f"[CANCELLED ORDER] Registrando en historial")

        from apps.orders.models import OrderHistory
        OrderHistory.objects.create(
            order=order,
            action='CANCEL_PROCESSED',
            previous_status=order.status,
            new_status='CANCELADO',
            reason='Procesamiento de cancelación completado'
        )


def get_order_process_template(order_type):
    """
    Factory para obtener template apropiado

    Args:
        order_type: 'new', 'ready', 'delivered', 'cancelled'

    Returns:
        OrderProcessTemplate apropiado
    """
    templates = {
        'new': NewOrderProcessTemplate(),
        'ready': ReadyOrderProcessTemplate(),
        'delivered': DeliveredOrderProcessTemplate(),
        'cancelled': CancelledOrderProcessTemplate()
    }

    return templates.get(order_type, NewOrderProcessTemplate())