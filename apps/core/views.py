"""
Vistas para Facade y operaciones centrales
Todas las operaciones ahora usan el Facade mejorado
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from .facade import get_facade


class RealizarPedidoCompletoView(APIView):
    """Vista para realizar pedido completo usando Facade"""

    def post(self, request):
        """
        Realizar pedido completo integrado

        Body: {
            "customer_id": 1,
            "table_number": 5,
            "mesero_id": 2,
            "items": [
                {
                    "product_id": 1,
                    "quantity": 2,
                    "extras": {
                        "leche": "deslactosada",
                        "azucar": "sin_azucar"
                    }
                }
            ],
            "special_instructions": "Sin azúcar"
        }
        """
        facade = get_facade()

        result = facade.crear_pedido_completo(
            customer_id=request.data['customer_id'],
            table_number=request.data['table_number'],
            items=request.data['items'],
            mesero_id=request.data.get('mesero_id'),
            instructions=request.data.get('special_instructions', '')
        )

        if result['success']:
            return Response(result, status=http_status.HTTP_201_CREATED)
        else:
            return Response(result, status=http_status.HTTP_400_BAD_REQUEST)


class CompletarOrdenView(APIView):
    """Completar orden (marcar como LISTO)"""

    def post(self, request, order_id):
        facade = get_facade()
        result = facade.completar_orden(order_id)

        if result['success']:
            return Response(result)
        else:
            return Response(result, status=http_status.HTTP_400_BAD_REQUEST)


class EntregarOrdenView(APIView):
    """Entregar orden (marcar como ENTREGADO)"""

    def post(self, request, order_id):
        facade = get_facade()
        result = facade.entregar_orden(order_id)

        if result['success']:
            return Response(result)
        else:
            return Response(result, status=http_status.HTTP_400_BAD_REQUEST)


class CancelarOrdenView(APIView):
    """Cancelar orden"""

    def post(self, request, order_id):
        facade = get_facade()

        result = facade.cancelar_orden(
            order_id=order_id,
            reason=request.data.get('reason', ''),
            user_id=request.data.get('user_id')
        )

        if result['success']:
            return Response(result)
        else:
            return Response(result, status=http_status.HTTP_400_BAD_REQUEST)


class EditarOrdenView(APIView):
    """Editar orden (solo si está PENDIENTE)"""

    def put(self, request, order_id):
        facade = get_facade()

        result = facade.editar_orden(
            order_id=order_id,
            new_items=request.data.get('items'),
            new_instructions=request.data.get('special_instructions')
        )

        if result['success']:
            return Response(result)
        else:
            return Response(result, status=http_status.HTTP_400_BAD_REQUEST)


class HistorialOrdenView(APIView):
    """Obtener historial completo de una orden"""

    def get(self, request, order_id):
        facade = get_facade()
        result = facade.obtener_historial_orden(order_id)

        if result['success']:
            return Response(result)
        else:
            return Response(result, status=http_status.HTTP_404_NOT_FOUND)


class ResumenOrdenView(APIView):
    """Obtener resumen completo de una orden"""

    def get(self, request, order_id):
        facade = get_facade()
        result = facade.obtener_resumen_orden(order_id)

        if result['success']:
            return Response(result)
        else:
            return Response(result, status=http_status.HTTP_404_NOT_FOUND)


class EstadoSistemaView(APIView):
    """Obtener estado general del sistema"""

    def get(self, request):
        facade = get_facade()
        estado = facade.obtener_estado_sistema()
        return Response(estado)


class EstadoCocinaView(APIView):
    """Obtener estado de cocina"""

    def get(self, request):
        facade = get_facade()
        result = facade.obtener_estado_cocina()
        return Response(result)


class MenuActualView(APIView):
    """Obtener menú actual"""

    def get(self, request):
        """
        Query params:
            - menu_type: 'standard', 'seasonal', 'quick'
        """
        facade = get_facade()
        menu_type = request.query_params.get('menu_type', 'standard')

        result = facade.obtener_menu_actual(menu_type)

        return Response(result)


class CambiarTemporadaView(APIView):
    """Cambiar temporada del menú"""

    def post(self, request):
        """
        Body: {
            "season": "INVIERNO" | "VERANO" | "OTONIO" | "PRIMAVERA" | "REGULAR"
        }
        """
        facade = get_facade()
        season = request.data.get('season')

        if not season:
            return Response({
                'error': 'Temporada requerida'
            }, status=http_status.HTTP_400_BAD_REQUEST)

        result = facade.cambiar_temporada(season)

        if result['success']:
            return Response(result)
        else:
            return Response(result, status=http_status.HTTP_400_BAD_REQUEST)


class NotificacionesUsuarioView(APIView):
    """Obtener notificaciones de un usuario"""

    def get(self, request, user_id):
        facade = get_facade()
        result = facade.obtener_notificaciones_usuario(user_id)

        if result['success']:
            return Response(result)
        else:
            return Response(result, status=http_status.HTTP_404_NOT_FOUND)


class DeshacerAccionView(APIView):
    """Deshacer última acción"""

    def post(self, request):
        facade = get_facade()
        result = facade.deshacer_ultima_accion()
        return Response(result)


class RehacerAccionView(APIView):
    """Rehacer acción"""

    def post(self, request):
        facade = get_facade()
        result = facade.rehacer_accion()
        return Response(result)


class LimpiarSistemaView(APIView):
    """Limpiar caches y datos temporales"""

    def post(self, request):
        facade = get_facade()
        result = facade.limpiar_sistema()
        return Response(result)