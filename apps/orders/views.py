"""
Vistas para órdenes
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Order
from .services import OrderService


class CreateOrderView(APIView):
    """Crear orden usando Builder"""

    def post(self, request):
        """
        Crear orden

        Body: {
            "customer_id": 1,
            "table_number": 5,
            "mesero_id": 2 (opcional),
            "items": [
                {"product_id": 1, "quantity": 2, "extras": {}},
                {"product_id": 3, "quantity": 1}
            ],
            "special_instructions": "Sin azúcar" (opcional)
        }
        """
        try:
            from apps.users.models import User

            customer = User.objects.get(id=request.data['customer_id'])
            mesero = None
            if 'mesero_id' in request.data:
                mesero = User.objects.get(id=request.data['mesero_id'])

            service = OrderService()
            order = service.create_order_with_builder(
                customer=customer,
                table_number=request.data['table_number'],
                items=request.data['items'],
                mesero=mesero,
                instructions=request.data.get('special_instructions', '')
            )

            return Response({
                'id': order.id,
                'status': order.status,
                'table': order.table_number,
                'total': float(order.total_price),
                'items_count': order.items.count()
            }, status=status.HTTP_201_CREATED)

        except User.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class AdvanceOrderView(APIView):
    """Avanzar orden al siguiente estado"""

    def post(self, request, order_id):
        try:
            service = OrderService()
            order = service.advance_order(order_id)

            return Response({
                'order_id': order.id,
                'new_status': order.status,
                'message': 'Estado actualizado'
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class CancelOrderView(APIView):
    """Cancelar orden"""

    def post(self, request, order_id):
        try:
            from apps.users.models import User

            reason = request.data.get('reason', '')
            user = None
            if 'user_id' in request.data:
                user = User.objects.get(id=request.data['user_id'])

            service = OrderService()
            order = service.cancel_order(order_id, reason, user)

            return Response({
                'order_id': order.id,
                'status': order.status,
                'message': 'Orden cancelada'
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class OrderHistoryView(APIView):
    """Ver historial de mementos de una orden"""

    def get(self, request, order_id):
        try:
            service = OrderService()
            history = service.get_order_history(order_id)

            return Response({
                'order_id': order_id,
                'history': history,
                'snapshots_count': len(history)
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class OrderDetailView(APIView):
    """Ver detalles de una orden"""

    def get(self, request, order_id):
        service = OrderService()
        details = service.get_order_details(order_id)

        if details:
            return Response(details)
        else:
            return Response(
                {'error': 'Orden no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )


class OrderListView(APIView):
    """Listar órdenes según estado"""

    def get(self, request):
        status_filter = request.query_params.get('status', None)

        service = OrderService()

        if status_filter == 'pending':
            orders = service.get_pending_orders()
        elif status_filter == 'in_preparation':
            orders = service.get_in_preparation_orders()
        elif status_filter == 'ready':
            orders = service.get_ready_orders()
        else:
            orders = Order.objects.all().order_by('-created_at')

        data = []
        for order in orders:
            data.append({
                'id': order.id,
                'customer': order.customer.username,
                'table': order.table_number,
                'status': order.status,
                'total': float(order.total_price),
                'created_at': order.created_at.isoformat()
            })

        return Response(data)