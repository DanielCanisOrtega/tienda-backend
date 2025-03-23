from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Tienda, Empleado, Producto, Venta, DetalleVenta, Gasto, Turno, AperturaCaja

# Obtener el modelo de usuario personalizado
Usuario = get_user_model()

# Serializador para Usuario
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'telefono']

# Serializador para Tienda
class TiendaSerializer(serializers.ModelSerializer):
    administrador = UsuarioSerializer(read_only=True)

    class Meta:
        model = Tienda
        fields = ['id', 'nombre', 'direccion', 'administrador']

# Serializador para Empleado
class EmpleadoSerializer(serializers.ModelSerializer):
    tienda = serializers.PrimaryKeyRelatedField(queryset=Tienda.objects.all())

    class Meta:
        model = Empleado
        fields = ['id', 'usuario', 'tienda']

# Serializador para Producto
class ProductoSerializer(serializers.ModelSerializer):
    tienda = serializers.PrimaryKeyRelatedField(queryset=Tienda.objects.all())

    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'categoria', 'precio', 'stock', 'codigo_barras', 'tienda']

# Serializador para Detalle de Venta
class DetalleVentaSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)

    class Meta:
        model = DetalleVenta
        fields = ['id', 'venta', 'producto', 'cantidad', 'subtotal']

# Serializador para Venta
class VentaSerializer(serializers.ModelSerializer):
    detalles = DetalleVentaSerializer(many=True, read_only=True)
    vendedor = UsuarioSerializer(read_only=True)

    class Meta:
        model = Venta
        fields = ['id', 'tienda', 'vendedor', 'fecha', 'total', 'detalles']

# Serializador para Gasto
class GastoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gasto
        fields = ['id', 'tienda', 'monto', 'categoria', 'descripcion', 'fecha']

# Serializador para Turno
class TurnoSerializer(serializers.ModelSerializer):
    empleado = UsuarioSerializer(read_only=True)

    class Meta:
        model = Turno
        fields = ['id', 'tienda', 'empleado', 'hora_inicio', 'hora_fin']

# Serializador para Apertura de Caja
class AperturaCajaSerializer(serializers.ModelSerializer):
    turno = TurnoSerializer(read_only=True)

    class Meta:
        model = AperturaCaja
        fields = ['id', 'tienda', 'turno', 'monto_inicial', 'fecha_apertura']
