"""
STRATEGY: Estrategias para diferentes canales de notificación
Permite cambiar dinámicamente el método de envío
"""
from abc import ABC, abstractmethod
from datetime import datetime


class NotificationStrategy(ABC):
    """Estrategia abstracta para enviar notificaciones"""

    @abstractmethod
    def send(self, recipient, message, **kwargs):
        """
        Enviar notificación

        Args:
            recipient: destinatario
            message: mensaje a enviar
            **kwargs: parámetros adicionales

        Returns:
            dict con resultado
        """
        pass

    @abstractmethod
    def get_type(self):
        """Tipo de estrategia"""
        pass

    def validate_recipient(self, recipient):
        """Validar destinatario"""
        return True

    def format_message(self, message, **kwargs):
        """Formatear mensaje según canal"""
        return message


class ConsoleNotificationStrategy(NotificationStrategy):
    """
    Estrategia de consola (para desarrollo y testing)
    """

    def send(self, recipient, message, **kwargs):
        """Imprimir en consola"""
        priority = kwargs.get('priority', 'normal')
        category = kwargs.get('category', 'general')

        icon = self._get_icon(category)

        print(f"\n{'='*60}")
        print(f"{icon} NOTIFICACIÓN [{priority.upper()}]")
        print(f"Para: {recipient}")
        print(f"Categoría: {category}")
        print(f"Mensaje: {message}")

        if 'order_id' in kwargs:
            print(f"Orden: #{kwargs['order_id']}")

        if 'table' in kwargs:
            print(f"Mesa: {kwargs['table']}")

        print(f"Hora: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}\n")

        return {
            'success': True,
            'type': 'console',
            'recipient': recipient,
            'timestamp': datetime.now().isoformat()
        }

    def _get_icon(self, category):
        """Obtener icono según categoría"""
        icons = {
            'order': '📋',
            'kitchen': '🍳',
            'ready': '✅',
            'alert': '⚠️',
            'error': '❌',
            'general': '📨'
        }
        return icons.get(category, '📨')

    def get_type(self):
        return 'console'


class EmailNotificationStrategy(NotificationStrategy):
    """
    Estrategia de email (simulada - integrar con servicio real)
    """

    def send(self, recipient, message, **kwargs):
        """Simular envío de email"""
        subject = kwargs.get('subject', 'Notificación - Café del Bosque')
        priority = kwargs.get('priority', 'normal')

        print(f"\n[EMAIL] Enviando a {recipient}")
        print(f"  Asunto: {subject}")
        print(f"  Prioridad: {priority}")
        print(f"  Mensaje: {message[:100]}...")

        # Aquí iría la integración real con servicio de email
        # Ejemplo: Django's send_mail, SendGrid, Mailgun, etc.
        """
        from django.core.mail import send_mail
        
        send_mail(
            subject=subject,
            message=message,
            from_email='notificaciones@cafedelbosque.com',
            recipient_list=[recipient],
            fail_silently=False,
        )
        """

        return {
            'success': True,
            'type': 'email',
            'recipient': recipient,
            'subject': subject,
            'timestamp': datetime.now().isoformat()
        }

    def validate_recipient(self, recipient):
        """Validar formato de email"""
        return '@' in recipient and '.' in recipient.split('@')[1]

    def get_type(self):
        return 'email'


class SMSNotificationStrategy(NotificationStrategy):
    """
    Estrategia de SMS (simulada - integrar con Twilio u otro)
    """

    def send(self, recipient, message, **kwargs):
        """Simular envío de SMS"""
        # Limitar mensaje a 160 caracteres
        sms_message = message[:160]

        print(f"\n[SMS] Enviando a {recipient}")
        print(f"  Mensaje ({len(sms_message)} chars): {sms_message}")

        # Aquí iría integración con servicio SMS
        """
        from twilio.rest import Client
        
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=sms_message,
            from_='+1234567890',
            to=recipient
        )
        """

        return {
            'success': True,
            'type': 'sms',
            'recipient': recipient,
            'message_length': len(sms_message),
            'timestamp': datetime.now().isoformat()
        }

    def validate_recipient(self, recipient):
        """Validar formato de teléfono"""
        # Remover caracteres no numéricos
        digits = ''.join(filter(str.isdigit, recipient))
        return len(digits) >= 10

    def format_message(self, message, **kwargs):
        """Limitar mensaje para SMS"""
        if len(message) > 160:
            return message[:157] + '...'
        return message

    def get_type(self):
        return 'sms'


class PushNotificationStrategy(NotificationStrategy):
    """
    Estrategia de notificaciones push (simulada - integrar con FCM, OneSignal, etc.)
    """

    def send(self, recipient, message, **kwargs):
        """Simular notificación push"""
        title = kwargs.get('title', 'Café del Bosque')
        priority = kwargs.get('priority', 'normal')
        data = kwargs.get('data', {})

        print(f"\n[PUSH] Enviando a {recipient}")
        print(f"  Título: {title}")
        print(f"  Mensaje: {message}")
        print(f"  Prioridad: {priority}")
        print(f"  Data: {data}")

        # Aquí iría integración con servicio push
        """
        import firebase_admin
        from firebase_admin import messaging
        
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=message,
            ),
            token=recipient,
            android=messaging.AndroidConfig(
                priority='high' if priority == 'high' else 'normal',
            ),
        )
        
        response = messaging.send(message)
        """

        return {
            'success': True,
            'type': 'push',
            'recipient': recipient,
            'title': title,
            'priority': priority,
            'timestamp': datetime.now().isoformat()
        }

    def get_type(self):
        return 'push'


class WebSocketNotificationStrategy(NotificationStrategy):
    """
    Estrategia de WebSocket (para notificaciones en tiempo real)
    """

    def send(self, recipient, message, **kwargs):
        """Enviar a través de WebSocket"""
        channel = kwargs.get('channel', 'notifications')
        event_type = kwargs.get('event_type', 'notification')

        print(f"\n[WEBSOCKET] Enviando a canal '{channel}'")
        print(f"  Destinatario: {recipient}")
        print(f"  Evento: {event_type}")
        print(f"  Mensaje: {message}")

        # Aquí iría integración con Django Channels o similar
        """
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            channel,
            {
                'type': event_type,
                'message': message,
                'recipient': recipient,
                **kwargs
            }
        )
        """

        return {
            'success': True,
            'type': 'websocket',
            'channel': channel,
            'recipient': recipient,
            'timestamp': datetime.now().isoformat()
        }

    def get_type(self):
        return 'websocket'


class InAppNotificationStrategy(NotificationStrategy):
    """
    Estrategia de notificaciones in-app (almacenadas en BD)
    """

    def send(self, recipient, message, **kwargs):
        """Guardar notificación en BD"""
        from apps.users.models import User

        print(f"\n[IN-APP] Guardando notificación para {recipient}")

        # Aquí se guardaría en un modelo de notificaciones
        """
        from apps.notifications.models import InAppNotification
        
        notification = InAppNotification.objects.create(
            user_id=recipient,
            message=message,
            category=kwargs.get('category', 'general'),
            priority=kwargs.get('priority', 'normal'),
            data=kwargs.get('data', {})
        )
        """

        return {
            'success': True,
            'type': 'in_app',
            'recipient': recipient,
            'timestamp': datetime.now().isoformat()
        }

    def get_type(self):
        return 'in_app'


class NotificationManager:
    """
    Manager que gestiona múltiples estrategias
    Permite envío multi-canal
    """

    _strategies = {
        'console': ConsoleNotificationStrategy(),
        'email': EmailNotificationStrategy(),
        'sms': SMSNotificationStrategy(),
        'push': PushNotificationStrategy(),
        'websocket': WebSocketNotificationStrategy(),
        'in_app': InAppNotificationStrategy()
    }

    @classmethod
    def send_notification(cls, strategy_type, recipient, message, **kwargs):
        """
        Enviar notificación usando estrategia específica

        Args:
            strategy_type: 'console', 'email', 'sms', 'push', 'websocket', 'in_app'
            recipient: destinatario
            message: mensaje a enviar
            **kwargs: parámetros adicionales

        Returns:
            dict con resultado del envío
        """
        strategy = cls._strategies.get(strategy_type, ConsoleNotificationStrategy())

        # Validar destinatario
        if not strategy.validate_recipient(recipient):
            return {
                'success': False,
                'error': f'Destinatario inválido para {strategy_type}',
                'type': strategy_type
            }

        # Formatear mensaje según canal
        formatted_message = strategy.format_message(message, **kwargs)

        # Enviar
        try:
            result = strategy.send(recipient, formatted_message, **kwargs)
            print(f"[MANAGER] ✓ Notificación enviada vía {strategy_type}")
            return result
        except Exception as e:
            print(f"[MANAGER] ✗ Error enviando vía {strategy_type}: {e}")
            return {
                'success': False,
                'error': str(e),
                'type': strategy_type
            }

    @classmethod
    def send_multi_channel(cls, recipient, message, channels=None, **kwargs):
        """
        Enviar notificación por múltiples canales

        Args:
            recipient: destinatario
            message: mensaje
            channels: lista de canales ['email', 'sms', 'push']
            **kwargs: parámetros adicionales

        Returns:
            dict con resultados por canal
        """
        if channels is None:
            channels = ['console']

        print(f"\n[MANAGER] === Enviando notificación multi-canal ===")
        print(f"Canales: {', '.join(channels)}")

        results = {}
        for channel in channels:
            if channel in cls._strategies:
                result = cls.send_notification(channel, recipient, message, **kwargs)
                results[channel] = result
            else:
                print(f"[MANAGER] ⚠️ Canal '{channel}' no disponible")
                results[channel] = {
                    'success': False,
                    'error': f'Canal {channel} no disponible'
                }

        success_count = sum(1 for r in results.values() if r.get('success'))
        print(f"[MANAGER] ✓ {success_count}/{len(channels)} canales exitosos\n")

        return results

    @classmethod
    def send_order_notification(cls, order, notification_type, channels=None):
        """
        Enviar notificación específica de orden

        Args:
            order: instancia de Order
            notification_type: 'new', 'ready', 'delivered', 'cancelled'
            channels: lista de canales

        Returns:
            dict con resultados
        """
        messages = {
            'new': f"Nueva orden #{order.id} recibida - Mesa {order.table_number}",
            'ready': f"Orden #{order.id} lista para servir - Mesa {order.table_number}",
            'delivered': f"Orden #{order.id} entregada exitosamente",
            'cancelled': f"Orden #{order.id} ha sido cancelada"
        }

        categories = {
            'new': 'order',
            'ready': 'ready',
            'delivered': 'order',
            'cancelled': 'alert'
        }

        priorities = {
            'new': 'high',
            'ready': 'high',
            'delivered': 'normal',
            'cancelled': 'medium'
        }

        message = messages.get(notification_type, f"Actualización de orden #{order.id}")
        category = categories.get(notification_type, 'general')
        priority = priorities.get(notification_type, 'normal')

        # Determinar destinatario
        if notification_type in ['new', 'cancelled']:
            # Notificar a cocina
            recipient = "cocina@cafedelbosque.com"
        elif notification_type == 'ready':
            # Notificar a mesero
            recipient = order.mesero.email if order.mesero else "meseros@cafedelbosque.com"
        else:
            # Notificar a cliente
            recipient = order.customer.email if order.customer.email else "cliente"

        return cls.send_multi_channel(
            recipient=recipient,
            message=message,
            channels=channels or ['console'],
            category=category,
            priority=priority,
            order_id=order.id,
            table=order.table_number
        )

    @classmethod
    def send_waiter_notification(cls, waiter, message, priority='normal', channels=None):
        """
        Enviar notificación a mesero

        Args:
            waiter: User mesero
            message: mensaje
            priority: prioridad
            channels: canales a usar
        """
        return cls.send_multi_channel(
            recipient=waiter.email,
            message=message,
            channels=channels or ['console', 'in_app'],
            category='waiter',
            priority=priority,
            waiter_id=waiter.id,
            waiter_name=waiter.username
        )

    @classmethod
    def send_customer_notification(cls, customer, message, priority='normal', channels=None):
        """
        Enviar notificación a cliente

        Args:
            customer: User cliente
            message: mensaje
            priority: prioridad
            channels: canales a usar
        """
        return cls.send_multi_channel(
            recipient=customer.email,
            message=message,
            channels=channels or ['console', 'in_app'],
            category='customer',
            priority=priority,
            customer_id=customer.id,
            customer_name=customer.username
        )

    @classmethod
    def send_kitchen_notification(cls, message, priority='high', channels=None):
        """
        Enviar notificación a cocina

        Args:
            message: mensaje
            priority: prioridad
            channels: canales a usar
        """
        return cls.send_multi_channel(
            recipient="cocina@cafedelbosque.com",
            message=message,
            channels=channels or ['console', 'websocket'],
            category='kitchen',
            priority=priority
        )

    @classmethod
    def get_available_strategies(cls):
        """Obtener estrategias disponibles"""
        return list(cls._strategies.keys())

    @classmethod
    def get_strategy_info(cls, strategy_type):
        """Obtener información de una estrategia"""
        strategy = cls._strategies.get(strategy_type)
        if strategy:
            return {
                'type': strategy.get_type(),
                'name': type(strategy).__name__,
                'available': True
            }
        return {
            'type': strategy_type,
            'available': False
        }

    @classmethod
    def test_strategy(cls, strategy_type):
        """
        Probar una estrategia

        Args:
            strategy_type: tipo de estrategia

        Returns:
            resultado del test
        """
        print(f"\n[MANAGER] === Probando estrategia: {strategy_type} ===")

        test_message = f"Mensaje de prueba para estrategia {strategy_type}"
        test_recipient = "test@cafedelbosque.com"

        result = cls.send_notification(
            strategy_type=strategy_type,
            recipient=test_recipient,
            message=test_message,
            category='test',
            priority='normal'
        )

        print(f"[MANAGER] Resultado: {'✓ Exitoso' if result.get('success') else '✗ Fallido'}\n")
        return result


class NotificationContext:
    """
    Contexto que permite cambiar estrategia dinámicamente
    """

    def __init__(self, strategy: NotificationStrategy = None):
        self._strategy = strategy or ConsoleNotificationStrategy()

    def set_strategy(self, strategy: NotificationStrategy):
        """Cambiar estrategia"""
        self._strategy = strategy
        print(f"[CONTEXT] Estrategia cambiada a: {strategy.get_type()}")

    def send(self, recipient, message, **kwargs):
        """Enviar usando estrategia actual"""
        return self._strategy.send(recipient, message, **kwargs)

    def get_current_strategy(self):
        """Obtener estrategia actual"""
        return self._strategy.get_type()