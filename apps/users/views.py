"""
Vistas para usuarios
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User
from .serializers import UserSerializer, UserDetailSerializer


class UserListView(APIView):
    """Listar todos los usuarios"""

    def get(self, request):
        role = request.query_params.get('role', None)

        if role:
            users = User.objects.filter(role=role)
        else:
            users = User.objects.all()

        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class UserDetailView(APIView):
    """Detalle de un usuario"""

    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            serializer = UserDetailSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )


class WaiterListView(APIView):
    """Listar meseros"""

    def get(self, request):
        waiters = User.objects.filter(role='MESERO')
        serializer = UserSerializer(waiters, many=True)
        return Response(serializer.data)


class ChefListView(APIView):
    """Listar cocineros"""

    def get(self, request):
        chefs = User.objects.filter(role='COCINERO')
        serializer = UserSerializer(chefs, many=True)
        return Response(serializer.data)