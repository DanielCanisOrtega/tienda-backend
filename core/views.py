from django.db import models
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import viewsets, permissions, status
from django.contrib.auth import get_user_model
from .models import Caja, Tienda, Empleado, Producto, Venta, DetalleVenta, Gasto
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
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
    """
    API para la gestión de tiendas.  
    Los usuarios pueden administrar sus tiendas, agregar y remover empleados, y seleccionar una tienda activa.
    """
    queryset = Tienda.objects.all()
    serializer_class = TiendaSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Lista las tiendas del usuario autenticado.",
        responses={200: TiendaSerializer(many=True)}
    )
    def get_queryset(self):
        """Filtra tiendas según el usuario autenticado"""
        return Tienda.objects.filter(propietario=self.request.user)

    @swagger_auto_schema(
        operation_description="Crea una nueva tienda y la asigna al usuario autenticado.",
        request_body=TiendaSerializer,
        responses={
            201: TiendaSerializer,
            400: "Error en la creación de la tienda."
        }
    )
    def perform_create(self, serializer):
        """Asigna automáticamente el propietario al usuario autenticado"""
        serializer.save(propietario=self.request.user)

    @swagger_auto_schema(
        operation_description="Lista los empleados de una tienda específica.",
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "empleados": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID del empleado"),
                                "nombre": openapi.Schema(type=openapi.TYPE_STRING, description="Nombre de usuario del empleado")
                            }
                        )
                    )
                }
            )
        }
    )
    @action(detail=True, methods=['get'])
    def empleados(self, request, pk=None):
        """Lista los empleados de una tienda específica"""
        tienda = self.get_object()
        empleados = Empleado.objects.filter(tienda=tienda)
        empleados_data = [
            {"id": empleado.id, "nombre": empleado.usuario.username}
            for empleado in empleados
        ]
        return Response({"empleados": empleados_data})

    @swagger_auto_schema(
        operation_description="Agrega un empleado a una tienda.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "usuario_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID del usuario a agregar")
            },
            required=["usuario_id"]
        ),
        responses={
            200: "Empleado agregado correctamente.",
            400: "Error en la asignación del empleado."
        }
    )
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

    @swagger_auto_schema(
        operation_description="Elimina un empleado de la tienda.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "usuario_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID del usuario a remover")
            },
            required=["usuario_id"]
        ),
        responses={
            200: "Empleado eliminado correctamente.",
            400: "El empleado no pertenece a esta tienda."
        }
    )
    @action(detail=True, methods=['post'])
    def remover_empleado(self, request, pk=None):
        """Elimina un empleado de la tienda"""
        tienda = self.get_object()
        usuario_id = request.data.get('usuario_id')

        try:
            empleado = Empleado.objects.get(usuario__id=usuario_id, tienda=tienda)
            empleado.delete()
            return Response({"mensaje": f"Empleado {empleado.usuario.username} eliminado de {tienda.nombre}"})

        except Empleado.DoesNotExist:
            return Response({"error": "El empleado no pertenece a esta tienda"}, status=400)

    @swagger_auto_schema(
        operation_description="Selecciona una tienda y la almacena en la sesión del usuario.",
        responses={200: "Tienda seleccionada correctamente.", 404: "Tienda no encontrada."}
    )
    @action(detail=True, methods=["post"])
    def seleccionar_tienda(self, request, pk=None):
        """
        Guarda en la sesión la tienda que el usuario está administrando.
        """
        tienda = get_object_or_404(Tienda, id=pk, propietario=request.user)
        request.session["tienda_id"] = tienda.id
        return Response({"mensaje": f"Tienda {tienda.nombre} seleccionada correctamente."})



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
    serializer_class = ProductoSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Lista los productos de la tienda activa del usuario.",
        responses={200: ProductoSerializer(many=True)}
    )
    def get_queryset(self):
        """
        Filtra los productos para que un usuario solo vea los de su tienda activa.
        """
        tienda_id = self.request.session.get("tienda_id")  # Obtener tienda activa de la sesión
        if not tienda_id:
            return Producto.objects.none()  # No retorna productos si no hay tienda activa
        
        return Producto.objects.filter(tienda_id=tienda_id)

    @swagger_auto_schema(
        operation_description="Crea un nuevo producto en la tienda activa.",
        request_body=ProductoSerializer,
        responses={
            201: ProductoSerializer,
            400: "No hay una tienda activa seleccionada."
        }
    )
    def perform_create(self, serializer):
        """
        Asigna automáticamente la tienda activa al crear un producto.
        """
        tienda_id = self.request.session.get("tienda_id")
        if not tienda_id:
            raise serializers.ValidationError("No hay una tienda activa seleccionada.")
        
        tienda = get_object_or_404(Tienda, id=tienda_id)
        serializer.save(tienda=tienda)

    @swagger_auto_schema(
        operation_description="Elimina un producto si no tiene ventas asociadas.",
        responses={
            204: "Producto eliminado correctamente.",
            400: "No se puede eliminar un producto con ventas asociadas."
        }
    )
    def destroy(self, request, *args, **kwargs):
        """
        Evita eliminar productos si tienen ventas asociadas.
        """
        producto = self.get_object()
        if producto.ventas.exists():  # Suponiendo que hay un modelo "Venta" con relación a "Producto"
            return Response({"error": "No se puede eliminar un producto con ventas asociadas."}, status=400)
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Actualiza la cantidad de stock de un producto en la tienda activa.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'cantidad': openapi.Schema(type=openapi.TYPE_INTEGER, description="Nueva cantidad de stock")
            },
            required=['cantidad']
        ),
        responses={
            200: "Cantidad actualizada correctamente.",
            400: "Debe proporcionar una cantidad válida o no hay tienda activa."
        }
    )
    @action(detail=True, methods=["patch"], url_path="actualizar-cantidad")
    def actualizar_cantidad(self, request, pk=None):
        """
        Permite actualizar la cantidad de stock de un producto, asegurando que pertenece a la tienda activa.
        """
        tienda_id = self.request.session.get("tienda_id")
        if not tienda_id:
            return Response({"error": "No hay una tienda activa seleccionada."}, status=400)

        producto = get_object_or_404(Producto, id=pk, tienda_id=tienda_id)  # Filtrar por tienda activa
        nueva_cantidad = request.data.get("cantidad")

        if nueva_cantidad is not None and isinstance(nueva_cantidad, int):
            producto.cantidad = nueva_cantidad
            producto.save()
            return Response({"mensaje": "Cantidad actualizada correctamente."})
        
        return Response({"error": "Debe proporcionar una cantidad válida."}, status=400)

    @swagger_auto_schema(
        operation_description="Obtiene una lista de productos con stock disponible en la tienda activa.",
        responses={200: ProductoSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path="disponibles")
    def productos_disponibles(self, request):
        """
        Retorna solo los productos con stock disponible.
        """
        tienda_id = self.request.session.get("tienda_id")  # Obtener tienda activa de la sesión
        if not tienda_id:
            return Producto.objects.none()  # No retorna productos si no hay tienda activa

        productos = Producto.objects.filter(tienda_id=tienda_id, cantidad__gt=0)
        serializer = self.get_serializer(productos, many=True)
        return Response(serializer.data)


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
    """
    API para gestionar los gastos de una tienda.
    """
    serializer_class = GastoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retorna los gastos de la tienda activa del usuario autenticado.
        """
        tienda_id = self.request.session.get("tienda_id")
        if not tienda_id:
            return Gasto.objects.none()  # No hay tienda seleccionada
        
        return Gasto.objects.filter(tienda_id=tienda_id)

    def perform_create(self, serializer):
        """
        Verifica que haya una caja abierta en la tienda y asigna automáticamente el gasto.
        """
        tienda_id = self.request.session.get("tienda_id")
        if not tienda_id:
            raise serializers.ValidationError("No hay una tienda activa seleccionada.")

        tienda = get_object_or_404(Tienda, id=tienda_id)

        # Verificar si hay una caja abierta en la tienda
        caja = Caja.objects.filter(tienda=tienda, estado="abierta").first()
        if not caja:
            raise serializers.ValidationError("No hay una caja abierta en la tienda.")

        # Guardar el gasto con la tienda, caja y usuario actual
        serializer.save(tienda=tienda, caja=caja, usuario=self.request.user)

    @action(detail=False, methods=['get'], url_path="por-categoria")
    def listar_por_categoria(self, request):
        """
        Retorna los gastos agrupados por categoría en la tienda activa.
        """
        tienda_id = self.request.session.get("tienda_id")
        if not tienda_id:
            return Response({"error": "No hay una tienda activa seleccionada."}, status=400)

        gastos = Gasto.objects.filter(tienda_id=tienda_id).values("categoria").annotate(total=models.Sum("monto"))
        return Response(gastos)

class CajaViewSet(viewsets.ModelViewSet):
    """
    API para gestionar la apertura y cierre de cajas.
    """
    serializer_class = CajaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retorna solo las cajas de la tienda activa en la sesión del usuario.
        """
        tienda_id = self.request.session.get("tienda_id")
        if not tienda_id:
            return Caja.objects.none()
        return Caja.objects.filter(tienda_id=tienda_id)

    def perform_create(self, serializer):  
        """
        Crea una nueva caja asegurando que no haya otra abierta en la tienda activa.
        """
        tienda_id = self.request.session.get("tienda_id")
        if not tienda_id:
            raise serializers.ValidationError("No hay una tienda activa seleccionada.")

        tienda = get_object_or_404(Tienda, id=tienda_id)
        
        # Verifica si hay una caja abierta en la tienda
        if Caja.objects.filter(tienda=tienda, estado='abierta').exists():
            raise serializers.ValidationError("Ya hay una caja abierta para esta tienda.")

        serializer.save(usuario=self.request.user, tienda=tienda)

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

