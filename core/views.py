from rest_framework import viewsets, permissions, status
from django.contrib.auth import get_user_model
from .models import Caja, Tienda, Empleado, Producto, Venta, DetalleVenta, Gasto
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    CajaSerializer, UsuarioSerializer, TiendaSerializer, EmpleadoSerializer, ProductoSerializer, VentaSerializer,
    DetalleVentaSerializer, GastoSerializer
)
from core import serializers

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

    def get_queryset(self):
        """Filtra tiendas según el usuario autenticado"""
        return Tienda.objects.filter(propietario=self.request.user)

    def perform_create(self, serializer):
        """Asigna automáticamente el propietario al usuario autenticado"""
        serializer.save(propietario=self.request.user)

    @action(detail=True, methods=['get'])
    def empleados(self, request, pk=None):
        """Lista los empleados de una tienda específica"""
        tienda = self.get_object()
        empleados = Empleado.objects.filter(tienda=tienda)  #  Filtrar empleados
        empleados_data = [
            {"id": empleado.id, "nombre": empleado.usuario.username}
            for empleado in empleados
        ]
        return Response({"empleados": empleados_data})

    @action(detail=True, methods=['post'])
    def agregar_empleado(self, request, pk=None):
        """Agrega un empleado a una tienda"""
        tienda = self.get_object()
        usuario_id = request.data.get('usuario_id')

        try:
            usuario = Usuario.objects.get(id=usuario_id)
            
            # Verificar si el usuario ya es empleado en esta tienda
            if Empleado.objects.filter(usuario=usuario, tienda=tienda).exists():
                return Response({"error": "El usuario ya es empleado en esta tienda"}, status=400)

            # Crear un nuevo empleado asociado a la tienda
            empleado = Empleado.objects.create(usuario=usuario, tienda=tienda)
            return Response({"mensaje": f"Empleado {usuario.username} agregado a {tienda.nombre}", "empleado_id": empleado.id})

        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=400)

    @action(detail=True, methods=['post'])
    def remover_empleado(self, request, pk=None):
        """Elimina un empleado de la tienda"""
        tienda = self.get_object()
        usuario_id = request.data.get('usuario_id')

        try:
            empleado = Empleado.objects.get(usuario__id=usuario_id, tienda=tienda)
            empleado.delete()  #  Eliminar correctamente el empleado
            return Response({"mensaje": f"Empleado {empleado.usuario.username} eliminado de {tienda.nombre}"})

        except Empleado.DoesNotExist:
            return Response({"error": "El empleado no pertenece a esta tienda"}, status=400)


# Vista para Empleados
class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer
    permission_classes = [permissions.IsAuthenticated]

# Vista para Productos
class ProductoViewSet(viewsets.ModelViewSet):
    """
    API para gestionar productos de una tienda.
    """
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filtra los productos para que un usuario solo vea los de su tienda.
        """
        return Producto.objects.filter(tienda__usuarios=self.request.user)

    def perform_create(self, serializer):
        """
        Asigna automáticamente la tienda del usuario autenticado al crear un producto.
        """
        tienda = self.request.user.tiendas.first()
        if not tienda:
            raise serializers.ValidationError("El usuario no tiene una tienda asignada.")
        serializer.save(tienda=tienda)

    def destroy(self, request, *args, **kwargs):
        """
        Evita eliminar productos si tienen ventas asociadas.
        """
        producto = self.get_object()
        if producto.ventas.exists():
            return Response({"error": "No se puede eliminar un producto con ventas asociadas."}, status=400)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['patch'], url_path="actualizar-cantidad")
    def actualizar_cantidad(self, request, pk=None):
        """
        Permite actualizar la cantidad de stock de un producto.
        """
        producto = self.get_object()
        nueva_cantidad = request.data.get("cantidad")
        if nueva_cantidad is not None:
            producto.cantidad = nueva_cantidad
            producto.save()
            return Response({"mensaje": "Cantidad actualizada correctamente."})
        return Response({"error": "Debe proporcionar una cantidad válida."}, status=400)

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
    """
    API para gestionar la apertura y cierre de cajas.
    """
    serializer_class = CajaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retorna solo las cajas de la tienda a la que pertenece el usuario autenticado.
        """
        return Caja.objects.filter(tienda__usuarios=self.request.user)

    def perform_create(self, serializer):
        """
        Crea una nueva caja asegurando que no haya otra abierta en la misma tienda.
        """
        tienda = serializer.validated_data['tienda']
        
        # Verifica si hay una caja abierta en la tienda
        if Caja.objects.filter(tienda=tienda, estado='abierta').exists():
            return Response(
                {"error": "Ya hay una caja abierta para esta tienda."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save(usuario=self.request.user)

    @action(detail=True, methods=['post'])
    def cerrar(self, request, pk=None):
        """
        Endpoint para cerrar una caja, requiere saldo final.
        """
        try:
            caja = self.get_object()
            
            if caja.estado == 'cerrada':
                return Response({"error": "La caja ya está cerrada."}, status=status.HTTP_400_BAD_REQUEST)
            
            saldo_final = request.data.get('saldo_final')
            
            if saldo_final is None:
                return Response({"error": "Debe proporcionar el saldo final."}, status=status.HTTP_400_BAD_REQUEST)

            caja.cerrar_caja(saldo_final)
            return Response({"mensaje": "Caja cerrada con éxito."}, status=status.HTTP_200_OK)
        
        except Caja.DoesNotExist:
            return Response({"error": "Caja no encontrada."}, status=status.HTTP_404_NOT_FOUND)

