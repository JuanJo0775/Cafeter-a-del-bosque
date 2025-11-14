"""
Vistas para cocina y estaciones
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.orders.models import Order
from .handlers import KitchenRouter


class RouteOrderView(APIView):
    """Enrutar orden a estaciones de cocina"""

    def post(self, request, order_id):
        """
        Enrutar orden a las estaciones correspondientes
        """
        try:
            order = Order.objects.get(id=order_id)

            router = KitchenRouter()
            assignments = router.route_order(order)

            return Response({
                'order_id': order.id,
                'table': order.table_number,
                'status': order.status,
                'assignments': assignments
            })

        except Order.DoesNotExist:
            return Response(
                {'error': 'Orden no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )


class StationStatusView(APIView):
    """Ver estado de estaciones de cocina"""

    def get(self, request):
        """Obtener estado de todas las estaciones"""
        router = KitchenRouter()
        status_data = router.get_station_status()

        return Response({
            'stations': status_data,
            'total_stations': len(status_data)
        })