"""
Vistas para menú
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Category, Product
from .services import MenuService, get_menu_factory


class CategoryListView(APIView):
    """Listar todas las categorías"""

    def get(self, request):
        categories = Category.objects.filter(is_active=True).prefetch_related('products')

        data = []
        for cat in categories:
            data.append({
                'id': cat.id,
                'name': cat.name,
                'type': cat.category_type,
                'description': cat.description,
                'products_count': cat.products.filter(is_available=True).count()
            })

        return Response(data)


class ProductListView(APIView):
    """Listar todos los productos"""

    def get(self, request):
        products = Product.objects.filter(is_available=True).select_related('category')

        data = []
        for prod in products:
            data.append({
                'id': prod.id,
                'name': prod.name,
                'description': prod.description,
                'category': prod.category.name,
                'base_price': float(prod.base_price),
                'preparation_time': prod.preparation_time,
                'available_extras': prod.available_extras
            })

        return Response(data)


class ProductDetailView(APIView):
    """Detalle de un producto"""

    def get(self, request, pk):
        try:
            product = Product.objects.select_related('category').get(pk=pk)

            return Response({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'category': {
                    'id': product.category.id,
                    'name': product.category.name,
                    'type': product.category.category_type
                },
                'base_price': float(product.base_price),
                'preparation_time': product.preparation_time,
                'available_extras': product.available_extras,
                'is_available': product.is_available
            })
        except Product.DoesNotExist:
            return Response(
                {'error': 'Producto no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )


class SeasonalMenuView(APIView):
    """
    Obtener menú según temporada (Abstract Factory)

    Query params:
        - season: regular, holiday, summer
        - time: breakfast, lunch, dinner
    """

    def get(self, request, season='regular'):
        time_of_day = request.query_params.get('time', 'lunch')

        factory = get_menu_factory(season)
        service = MenuService(factory)

        categories = service.get_menu_by_time(time_of_day)

        menu_data = []
        for cat in categories:
            products = cat.products.filter(is_available=True)
            priced_products = service.apply_pricing(products)

            menu_data.append({
                'category': cat.name,
                'type': cat.category_type,
                'products': priced_products
            })

        return Response({
            'season': season,
            'time_of_day': time_of_day,
            'menu': menu_data
        })


class TimeBasedMenuView(APIView):
    """Obtener menú según hora del día"""

    def get(self, request, time='lunch'):
        service = MenuService()
        categories = service.get_menu_by_time(time)

        menu_data = []
        for cat in categories:
            menu_data.append({
                'id': cat.id,
                'name': cat.name,
                'type': cat.category_type,
                'products': [
                    {
                        'id': p.id,
                        'name': p.name,
                        'price': float(p.base_price)
                    }
                    for p in cat.products.filter(is_available=True)
                ]
            })

        return Response({
            'time_of_day': time,
            'menu': menu_data
        })