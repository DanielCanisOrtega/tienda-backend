from rest_framework import viewsets, permissions
from django.contrib.auth import get_user_model
from .models import Caja, Tienda, Empleado, Producto, Venta, DetalleVenta, Gasto
from rest_framework.decorators import action
from .serializers import (
    CajaSerializer, UsuarioSerializer, TiendaSerializer, EmpleadoSerializer, ProductoSerializer, VentaSerializer,
    DetalleVentaSerializer, GastoSerializer
)

# Obtener el modelo de usuario
Usuario = get_user_model()

# Vista para Usuarios
class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.IsAuthenticated]

# Vista para Tiendas
class TiendaViewSet(viewsets.ModelViewSet):
    queryset = Tienda.objects.all()
    serializer_class = TiendaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(administrador=self.request.user)

# Vista para Empleados
class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer
    permission_classes = [permissions.IsAuthenticated]

# Vista para Productos
class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [permissions.IsAuthenticated]

# Vista para Ventas
class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all()
    serializer_class = VentaSerializer
    permission_classes = [permissions.IsAuthenticated]

# Vista para Detalles de Ventas
class DetalleVentaViewSet(viewsets.ModelViewSet):
    queryset = DetalleVenta.objects.all()
    serializer_class = DetalleVentaSerializer
    permission_classes = [permissions.IsAuthenticated]

# Vista para Gastos
class GastoViewSet(viewsets.ModelViewSet):
    queryset = Gasto.objects.all()
    serializer_class = GastoSerializer
    permission_classes = [permissions.IsAuthenticated]

class CajaViewSet(viewsets.ModelViewSet):
    queryset = Caja.objects.all()
    serializer_class = CajaSerializer

    def get_queryset(self):
        return Caja.objects.filter(tienda=self.request.user.tienda_actual)

    @action(detail=True, methods=['post'])
    def cerrar_caja(self, request, pk=None):
        caja = self.get_object()
        if caja.estado == 'cerrada':
            return Response({"error": "La caja ya está cerrada."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = CajaCierreSerializer(data=request.data)
        if serializer.is_valid():
            caja.cerrar_caja(serializer.validated_data['saldo_final'])
            return Response(CajaSerializer(caja).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

