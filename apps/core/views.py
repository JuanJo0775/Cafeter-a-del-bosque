"""
Vistas para Facade y operaciones centrales
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .facade import CafeteriaFacade
from .config import get_config
from .cache_proxy import MenuProxy


class RealizarPedidoCompletoView(APIView):
    """Vista para realizar pedido completo usando Facade"""

    def post(self, request):
        """
        Realizar pedido completo: crear + notificar + enrutar

        Body: {
            "customer_id": 1,
            "table_number": 5,
            "mesero_id": 2,
            "items": [
                {"product_id": 1, "quantity": 2, "extras": {}},
                {"product_id": 3, "quantity": 1}
            ]
        }
        """
        facade = CafeteriaFacade()

        result = facade.realizar_pedido_completo(
            customer_id=request.data['customer_id'],
            table_number=request.data['table_number'],
            items=request.data['items'],
            mesero_id=request.data.get('mesero_id')
        )

        if result['success']:
            return Response(result, status=status.HTTP_201_CREATED)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class CompletarOrdenView(APIView):
    """Completar orden (marcar como LISTO)"""

    def post(self, request, order_id):
        facade = CafeteriaFacade()
        result = facade.completar_orden(order_id)

        if result['success']:
            return Response(result)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class EntregarOrdenView(APIView):
    """Entregar orden (marcar como ENTREGADO)"""

    def post(self, request, order_id):
        facade = CafeteriaFacade()
        result = facade.entregar_orden(order_id)

        if result['success']:
            return Response(result)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class EstadoSistemaView(APIView):
    """Obtener estado general del sistema"""

    def get(self, request):
        facade = CafeteriaFacade()
        estado = facade.obtener_estado_sistema()
        return Response(estado)


class ConfiguracionView(APIView):
    """Obtener/actualizar configuración (Singleton)"""

    def get(self, request):
        """Obtener configuración actual"""
        config = get_config()
        return Response(config.get_config())

    def patch(self, request):
        """Actualizar configuración"""
        config = get_config()
        config.update_config(**request.data)
        return Response({
            'message': 'Configuración actualizada',
            'config': config.get_config()
        })


class MenuCachedView(APIView):
    """Obtener menú desde cache (Proxy)"""

    def get(self, request):
        """Obtener menú cacheado"""
        proxy = MenuProxy()
        force_refresh = request.query_params.get('refresh', 'false').lower() == 'true'

        menu = proxy.get_menu(force_refresh=force_refresh)
        cache_info = proxy.get_cache_info()

        return Response({
            'menu': menu,
            'cache_info': cache_info
        })

    def delete(self, request):
        """Invalidar cache del menú"""
        proxy = MenuProxy()
        proxy.invalidate_cache()
        return Response({
            'message': 'Cache invalidado'
        })


class BuscarProductoView(APIView):
    """Buscar productos en cache"""

    def get(self, request):
        query = request.query_params.get('q', '')

        if not query:
            return Response({
                'error': 'Parámetro "q" requerido'
            }, status=status.HTTP_400_BAD_REQUEST)

        proxy = MenuProxy()
        results = proxy.search_products(query)

        return Response({
            'query': query,
            'results': results,
            'count': len(results)
        })