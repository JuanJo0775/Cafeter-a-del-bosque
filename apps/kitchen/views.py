"""
Vistas para gestión de cocina y estaciones
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.orders.models import Order
from .handlers import KitchenRouter
from .models import KitchenStation, StationQueue


class RouteOrderView(APIView):
    """Enrutar orden completa a estaciones"""

    def post(self, request, order_id):
        """Enrutar orden a las estaciones correspondientes"""
        try:
            order = Order.objects.get(id=order_id)

            # Verificar que esté en estado correcto
            if order.status not in ['PENDIENTE', 'EN_PREPARACION']:
                return Response({
                    'error': f'No se puede enrutar orden en estado {order.status}'
                }, status=status.HTTP_400_BAD_REQUEST)

            router = KitchenRouter()
            assignments = router.route_order(order)

            return Response({
                'order_id': order.id,
                'table': order.table_number,
                'status': order.status,
                'assignments': assignments,
                'stations_count': len(assignments)
            })

        except Order.DoesNotExist:
            return Response(
                {'error': 'Orden no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )


class StationStatusView(APIView):
    """Ver estado de todas las estaciones"""

    def get(self, request):
        """Obtener estado completo de estaciones"""
        router = KitchenRouter()
        status_data = router.get_station_status()

        return Response({
            'stations': status_data,
            'total_stations': len(status_data),
            'timestamp': datetime.now().isoformat()
        })


class StationQueueView(APIView):
    """Ver cola de una estación específica"""

    def get(self, request, station_type):
        """Obtener cola de estación"""
        router = KitchenRouter()
        queue = router.get_station_queue(station_type)

        queue_data = []
        for item in queue:
            queue_data.append({
                'order_id': item.order.id,
                'table': item.order.table_number,
                'assigned_at': item.assigned_at.isoformat(),
                'waiting_time_minutes': item.get_waiting_time(),
                'is_delayed': item.is_delayed(),
                'items_count': item.order.items.count()
            })

        return Response({
            'station_type': station_type,
            'queue': queue_data,
            'pending_count': len(queue_data)
        })


class CompleteStationItemView(APIView):
    """Marcar item como completado en estación"""

    def post(self, request, station_type, order_id):
        """Completar item en estación"""
        router = KitchenRouter()
        success = router.complete_station_item(station_type, order_id)

        if success:
            return Response({
                'success': True,
                'message': f'Orden #{order_id} completada en estación',
                'station_type': station_type
            })
        else:
            return Response({
                'success': False,
                'error': 'No se pudo completar item'
            }, status=status.HTTP_400_BAD_REQUEST)


class ChainInfoView(APIView):
    """Información de la cadena de handlers"""

    def get(self, request):
        """Obtener info de la cadena"""
        router = KitchenRouter()
        chain_info = router.get_chain_info()

        return Response(chain_info)