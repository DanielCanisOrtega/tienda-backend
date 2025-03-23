from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Tienda, Empleado, Producto, Venta, DetalleVenta, Gasto, Caja

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

class CajaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caja
        fields = '__all__'

class CajaCierreSerializer(serializers.ModelSerializer):
    saldo_final = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = Caja
        fields = ['saldo_final']
