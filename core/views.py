from django.db import models
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import viewsets, permissions, status
from django.contrib.auth import get_user_model
from .models import Caja, Tienda, Empleado, Producto, Venta, DetalleVenta, Gasto
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
import random
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

    def perform_create(self, serializer):
        # Generar una contraseña aleatoria temporal
        password_temporal = get_random_string(length=8)  # Ej: 'A2k9Lm3p'
        
        # Guardar el usuario con contraseña encriptada
        usuario = serializer.save(password=make_password(password_temporal))

        # Guardar la contraseña temporal en el objeto para retornarla en la respuesta
        self.password_temporal = password_temporal

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)

        # Solo si el usuario se creó correctamente
        if hasattr(self, 'password_temporal'):
            response.data['password_temporal'] = self.password_temporal
        
        return response

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
        """Crea un nuevo usuario como empleado en la tienda activa."""
        tienda = self.get_object()
        nombre = request.data.get('nombre')
        password_temporal = 'test'
    

        if not nombre:
            return Response({"error": "El nombre del empleado es obligatorio."}, status=400)

        # Crear el usuario con la contraseña temporal
        usuario = Usuario.objects.create(
            username=nombre,
            password=make_password(password_temporal)  # Asegura que la contraseña se almacene encriptada
        )
    

        # Asociar el usuario como empleado de la tienda
        Empleado.objects.create(usuario=usuario, tienda=tienda)

        return Response({
            "mensaje": f"Empleado {usuario.username} agregado a {tienda.nombre}.",
            "empleado_id": usuario.id,
            "password_temporal": usuario.password
        })

    
    @swagger_auto_schema(
    operation_description="Elimina un empleado de la tienda.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "empleado_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID del empleado a remover")
        },
        required=["empleado_id"]
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
        empleado_id = request.data.get('empleado_id')

        if not empleado_id:
            return Response({"error": "Debe proporcionar el ID del empleado a eliminar."}, status=400)

        try:
            empleado = Empleado.objects.get(id=empleado_id, tienda=tienda)
            nombre_empleado = empleado.usuario.username
            empleado.delete()
            return Response({"mensaje": f"Empleado {nombre_empleado} fue eliminado de {tienda.nombre}."})

        except Empleado.DoesNotExist:
            return Response({"error": "El empleado no pertenece a esta tienda o no existe."}, status=400)


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
    serializer_class = ProductoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        tienda_id = self.request.query_params.get("tienda_id")
        if not tienda_id:
            return Producto.objects.none()
        return Producto.objects.filter(tienda_id=tienda_id)

    def perform_create(self, serializer):
        tienda_id = self.request.data.get("tienda_id")
        if not tienda_id:
            raise serializers.ValidationError("Debe proporcionar el ID de la tienda.")
        tienda = get_object_or_404(Tienda, id=tienda_id)
        serializer.save(tienda=tienda)

    def destroy(self, request, *args, **kwargs):
        tienda_id = self.request.query_params.get("tienda_id")
        producto = get_object_or_404(Producto, id=kwargs["pk"], tienda_id=tienda_id)
        if producto.ventas.exists():
            return Response({"error": "No se puede eliminar un producto con ventas asociadas."}, status=400)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["patch"], url_path="actualizar-cantidad")
    def actualizar_cantidad(self, request, pk=None):
        tienda_id = request.data.get("tienda_id")
        if not tienda_id:
            return Response({"error": "Debe proporcionar el ID de la tienda."}, status=400)
        producto = get_object_or_404(Producto, id=pk, tienda_id=tienda_id)
        nueva_cantidad = request.data.get("cantidad")
        if nueva_cantidad is not None and isinstance(nueva_cantidad, int):
            producto.cantidad = nueva_cantidad
            producto.save()
            return Response({"mensaje": "Cantidad actualizada correctamente."})
        return Response({"error": "Debe proporcionar una cantidad válida."}, status=400)

    @action(detail=False, methods=['get'], url_path="disponibles")
    def productos_disponibles(self, request):
        tienda_id = request.query_params.get("tienda_id")
        if not tienda_id:
            return Producto.objects.none()
        productos = Producto.objects.filter(tienda_id=tienda_id, cantidad__gt=0)
        serializer = self.get_serializer(productos, many=True)
        return Response(serializer.data)


# Vista para Ventas
class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all()
    serializer_class = VentaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        usuario = self.request.user
        tienda = self.request.query_params.get("tienda")
        queryset = Venta.objects.filter(usuario=usuario)
        if tienda:
            queryset = queryset.filter(tienda_id=tienda)
        return queryset.order_by('-fecha')

    def create(self, request, *args, **kwargs):
        usuario = request.user
        tienda_id = request.data.get("tienda")
        productos = request.data.get("productos")  # [{producto, cantidad}]

        # Verifica caja abierta
        caja = Caja.objects.filter(tienda_id=tienda_id, usuario=usuario, estado='abierta').first()
        if not caja:
            return Response({"error": "No hay caja abierta para esta tienda."}, status=status.HTTP_400_BAD_REQUEST)

        detalles = []
        total = 0

        for item in productos:
            try:
                producto = Producto.objects.get(pk=item["producto"])
                cantidad = int(item["cantidad"])
                if producto.cantidad < cantidad:
                    return Response(
                        {"error": f"Stock insuficiente para {producto.nombre}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                subtotal = producto.precio * cantidad
                total += subtotal
                detalles.append({
                    "producto": producto,
                    "cantidad": cantidad,
                    "precio_unitario": producto.precio,
                    "subtotal": subtotal,
                })

                producto.cantidad -= cantidad
                producto.save()

            except Producto.DoesNotExist:
                return Response({"error": f"Producto con ID {item['producto']} no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        venta = Venta.objects.create(tienda_id=tienda_id, caja=caja, usuario=usuario, total=total)

        for d in detalles:
            DetalleVenta.objects.create(
                venta=venta,
                producto=d["producto"],
                cantidad=d["cantidad"],
                precio_unitario=d["precio_unitario"],
                subtotal=d["subtotal"]
            )

        return Response(VentaSerializer(venta).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def total_hoy(self, request):
        hoy = now().date()
        ventas = Venta.objects.filter(usuario=request.user, fecha__date=hoy)
        total = sum(v.total for v in ventas)
        return Response({"fecha": str(hoy), "total_ventas": total})

# Vista para Detalles de Ventas
class DetalleVentaViewSet(viewsets.ModelViewSet):
    queryset = DetalleVenta.objects.all()
    serializer_class = DetalleVentaSerializer
    permission_classes = [permissions.IsAuthenticated]

# Vista para Gastos
class GastoViewSet(viewsets.ModelViewSet):
    serializer_class = GastoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        tienda_id = self.request.query_params.get("tienda_id")
        if not tienda_id:
            return Gasto.objects.none()
        return Gasto.objects.filter(tienda_id=tienda_id)

    def perform_create(self, serializer):
        tienda_id = self.request.data.get("tienda_id")
        if not tienda_id:
            raise serializers.ValidationError("Debe proporcionar el ID de la tienda.")
        tienda = get_object_or_404(Tienda, id=tienda_id)
        caja = Caja.objects.filter(tienda=tienda, estado="abierta").first()
        if not caja:
            raise serializers.ValidationError("No hay una caja abierta en la tienda.")
        serializer.save(tienda=tienda, caja=caja, usuario=self.request.user)

    @action(detail=False, methods=['get'], url_path="por-categoria")
    def listar_por_categoria(self, request):
        tienda_id = request.query_params.get("tienda_id")
        if not tienda_id:
            return Response({"error": "Debe proporcionar el ID de la tienda."}, status=400)
        gastos = Gasto.objects.filter(tienda_id=tienda_id).values("categoria").annotate(total=models.Sum("monto"))
        return Response(gastos)


class CajaViewSet(viewsets.ModelViewSet):
    serializer_class = CajaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        tienda_id = self.request.query_params.get("tienda_id")
        if not tienda_id:
            return Caja.objects.none()
        return Caja.objects.filter(tienda_id=tienda_id)

    def perform_create(self, serializer):
        tienda_id = self.request.data.get("tienda_id")
        if not tienda_id:
            raise serializers.ValidationError("Debe proporcionar el ID de la tienda.")
        tienda = get_object_or_404(Tienda, id=tienda_id)
        if Caja.objects.filter(tienda=tienda, estado='abierta').exists():
            raise serializers.ValidationError("Ya hay una caja abierta para esta tienda.")
        serializer.save(usuario=self.request.user, tienda=tienda)

    @action(detail=True, methods=['post'])
    def cerrar(self, request, pk=None):
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

