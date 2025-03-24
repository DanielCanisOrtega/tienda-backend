from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Usuario, Tienda, Empleado, Producto, Venta, DetalleVenta, Gasto, Caja

# Obtener el modelo de usuario personalizado
#Usuario = get_user_model()

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
        fields = ['id', 'nombre', 'categoria', 'precio', 'cantidad', 'codigo_barras', 'tienda']

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
        fields = '__all__'  # Muestra todos los campos
        read_only_fields = ['fecha_apertura', 'fecha_cierre', 'estado']

    def update(self, instance, validated_data):
        """
        Permite actualizar solo ciertos campos de la caja (evita modificar estado manualmente).
        """
        if 'saldo_final' in validated_data:
            instance.cerrar_caja(validated_data['saldo_final'])
        return super().update(instance, validated_data)