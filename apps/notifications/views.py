"""
Vistas para gestión de notificaciones
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.users.models import User
from .services import NotificationService
from .strategies import NotificationManager


class RegisterObserverView(APIView):
    """Registrar usuario como observer"""

    def post(self, request):
        """
        Registrar observer

        Body: {
            "user_id": 1,
            "observer_type": "waiter" | "chef" | "customer",
            "station_type": "BEBIDAS_CALIENTES" (solo para chefs)
        }
        """
        try:
            user_id = request.data.get('user_id')
            observer_type = request.data.get('observer_type')
            station_type = request.data.get('station_type')

            user = User.objects.get(id=user_id)

            if observer_type == 'waiter':
                NotificationService.register_waiter(user)
            elif observer_type == 'chef':
                NotificationService.register_chef(user, station_type)
            elif observer_type == 'customer':
                NotificationService.register_customer(user)
            else:
                return Response({
                    'error': 'Tipo de observer inválido'
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'success': True,
                'message': f'{observer_type.title()} registrado',
                'user_id': user.id,
                'username': user.username
            })

        except User.DoesNotExist:
            return Response({
                'error': 'Usuario no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class UnregisterObserverView(APIView):
    """Desregistrar observer"""

    def post(self, request):
        """
        Desregistrar observer

        Body: {
            "user_id": 1,
            "observer_type": "waiter" | "chef" | "customer"
        }
        """
        try:
            user_id = request.data.get('user_id')
            observer_type = request.data.get('observer_type')

            user = User.objects.get(id=user_id)

            if observer_type == 'waiter':
                NotificationService.unregister_waiter(user)
            elif observer_type == 'chef':
                NotificationService.unregister_chef(user)
            elif observer_type == 'customer':
                NotificationService.unregister_customer(user)
            else:
                return Response({
                    'error': 'Tipo de observer inválido'
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'success': True,
                'message': f'{observer_type.title()} desregistrado',
                'user_id': user.id
            })

        except User.DoesNotExist:
            return Response({
                'error': 'Usuario no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class GetNotificationsView(APIView):
    """Obtener notificaciones de un usuario"""

    def get(self, request, user_id):
        """Obtener notificaciones según rol del usuario"""
        try:
            user = User.objects.get(id=user_id)

            if user.role == 'MESERO':
                notifications = NotificationService.get_waiter_notifications(user)
            elif user.role == 'COCINERO':
                notifications = NotificationService.get_chef_notifications(user)
            elif user.role == 'CLIENTE':
                notifications = NotificationService.get_customer_notifications(user)
            else:
                notifications = []

            return Response({
                'user_id': user.id,
                'username': user.username,
                'role': user.role,
                'notifications': notifications,
                'count': len(notifications),
                'unread_count': len([n for n in notifications if not n.get('read', False)])
            })

        except User.DoesNotExist:
            return Response({
                'error': 'Usuario no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)


class GetKitchenNotificationsView(APIView):
    """Obtener notificaciones de cocina"""

    def get(self, request):
        """Obtener todas las notificaciones de cocina"""
        notifications = NotificationService.get_kitchen_notifications()

        return Response({
            'notifications': notifications,
            'count': len(notifications),
            'unread_count': len([n for n in notifications if not n.get('read', False)])
        })


class SendNotificationView(APIView):
    """Enviar notificación usando estrategia específica"""

    def post(self, request):
        """
        Enviar notificación

        Body: {
            "strategy": "console" | "email" | "sms" | "push",
            "recipient": "email@example.com",
            "message": "Mensaje a enviar",
            "priority": "high" | "normal" | "low",
            "category": "order" | "kitchen" | "alert"
        }
        """
        strategy = request.data.get('strategy', 'console')
        recipient = request.data.get('recipient')
        message = request.data.get('message')
        priority = request.data.get('priority', 'normal')
        category = request.data.get('category', 'general')

        if not recipient or not message:
            return Response({
                'error': 'Destinatario y mensaje son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)

        result = NotificationManager.send_notification(
            strategy_type=strategy,
            recipient=recipient,
            message=message,
            priority=priority,
            category=category
        )

        if result.get('success'):
            return Response(result)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class SendMultiChannelNotificationView(APIView):
    """Enviar notificación por múltiples canales"""

    def post(self, request):
        """
        Enviar multi-canal

        Body: {
            "recipient": "email@example.com",
            "message": "Mensaje",
            "channels": ["console", "email", "sms"],
            "priority": "high"
        }
        """
        recipient = request.data.get('recipient')
        message = request.data.get('message')
        channels = request.data.get('channels', ['console'])
        priority = request.data.get('priority', 'normal')

        if not recipient or not message:
            return Response({
                'error': 'Destinatario y mensaje son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)

        results = NotificationManager.send_multi_channel(
            recipient=recipient,
            message=message,
            channels=channels,
            priority=priority
        )

        return Response({
            'results': results,
            'total_channels': len(channels),
            'successful_channels': sum(1 for r in results.values() if r.get('success'))
        })


class ServiceStatsView(APIView):
    """Estadísticas del servicio de notificaciones"""

    def get(self, request):
        """Obtener estadísticas"""
        stats = NotificationService.get_service_stats()

        return Response(stats)


class AvailableStrategiesView(APIView):
    """Listar estrategias disponibles"""

    def get(self, request):
        """Obtener estrategias disponibles"""
        strategies = NotificationManager.get_available_strategies()

        strategies_info = []
        for strategy in strategies:
            info = NotificationManager.get_strategy_info(strategy)
            strategies_info.append(info)

        return Response({
            'strategies': strategies_info,
            'count': len(strategies)
        })


class TestStrategyView(APIView):
    """Probar una estrategia"""

    def post(self, request):
        """
        Probar estrategia

        Body: {
            "strategy": "console" | "email" | "sms"
        }
        """
        strategy = request.data.get('strategy', 'console')

        result = NotificationManager.test_strategy(strategy)

        return Response(result)


class ClearNotificationsView(APIView):
    """Limpiar notificaciones"""

    def post(self, request):
        """Limpiar todas las notificaciones"""
        NotificationService.clear_all_notifications()

        return Response({
            'success': True,
            'message': 'Todas las notificaciones limpiadas'
        })