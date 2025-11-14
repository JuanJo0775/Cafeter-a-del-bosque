"""
Patrón STRATEGY para diferentes métodos de notificación
"""
from abc import ABC, abstractmethod


class NotificationStrategy(ABC):
    """Estrategia abstracta para enviar notificaciones"""

    @abstractmethod
    def send(self, recipient, message):
        """Enviar notificación"""
        pass

    @abstractmethod
    def get_type(self):
        """Obtener tipo de notificación"""
        pass


class ConsoleNotificationStrategy(NotificationStrategy):
    """Estrategia de notificación por consola (para desarrollo)"""

    def send(self, recipient, message):
        """Imprimir en consola"""
        print(f"[CONSOLE NOTIFICATION] To: {recipient} | Message: {message}")
        return {
            'success': True,
            'type': 'console',
            'recipient': recipient
        }

    def get_type(self):
        return 'console'


class EmailNotificationStrategy(NotificationStrategy):
    """Estrategia de notificación por email (simulada)"""

    def send(self, recipient, message):
        """Simular envío de email"""
        print(f"[EMAIL] Sending to {recipient}:")
        print(f"  Subject: Café del Bosque - Notificación")
        print(f"  Body: {message}")

        # Aquí iría la lógica real de envío de email
        # Ej: usar Django's send_mail o servicio externo

        return {
            'success': True,
            'type': 'email',
            'recipient': recipient,
            'message': message
        }

    def get_type(self):
        return 'email'


class SMSNotificationStrategy(NotificationStrategy):
    """Estrategia de notificación por SMS (simulada)"""

    def send(self, recipient, message):
        """Simular envío de SMS"""
        print(f"[SMS] Sending to {recipient}:")
        print(f"  Message: {message[:160]}")  # SMS limitado a 160 caracteres

        # Aquí iría integración con servicio de SMS (Twilio, etc.)

        return {
            'success': True,
            'type': 'sms',
            'recipient': recipient,
            'message_length': len(message)
        }

    def get_type(self):
        return 'sms'


class PushNotificationStrategy(NotificationStrategy):
    """Estrategia de notificación push (simulada)"""

    def send(self, recipient, message):
        """Simular notificación push"""
        print(f"[PUSH] Sending to {recipient}:")
        print(f"  Title: Nueva Notificación")
        print(f"  Body: {message}")

        # Aquí iría integración con FCM, OneSignal, etc.

        return {
            'success': True,
            'type': 'push',
            'recipient': recipient,
            'priority': 'high'
        }

    def get_type(self):
        return 'push'


class NotificationManager:
    """
    Manager que selecciona la estrategia apropiada
    """

    _strategies = {
        'console': ConsoleNotificationStrategy(),
        'email': EmailNotificationStrategy(),
        'sms': SMSNotificationStrategy(),
        'push': PushNotificationStrategy(),
    }

    @classmethod
    def send_notification(cls, strategy_type, recipient, message):
        """
        Enviar notificación usando la estrategia especificada

        Args:
            strategy_type: 'console', 'email', 'sms', 'push'
            recipient: destinatario
            message: mensaje a enviar

        Returns:
            resultado del envío
        """
        strategy = cls._strategies.get(strategy_type, ConsoleNotificationStrategy())
        return strategy.send(recipient, message)

    @classmethod
    def send_multi_channel(cls, recipient, message, channels=None):
        """
        Enviar notificación por múltiples canales

        Args:
            recipient: destinatario
            message: mensaje
            channels: lista de canales ['email', 'sms', 'push']

        Returns:
            dict con resultados de cada canal
        """
        if channels is None:
            channels = ['console']

        results = {}
        for channel in channels:
            if channel in cls._strategies:
                results[channel] = cls._strategies[channel].send(recipient, message)

        return results

    @classmethod
    def get_available_strategies(cls):
        """Obtener estrategias disponibles"""
        return list(cls._strategies.keys())