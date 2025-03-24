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
    propietario = UsuarioSerializer(read_only=True)
    empleados = serializers.SerializerMethodField()  # Agrega una función para obtener empleados específicos

    class Meta:
        model = Tienda
        fields = ['id', 'nombre', 'direccion', 'propietario', 'empleados']

    def get_empleados(self, obj):
        """Obtiene los empleados pertenecientes a la tienda específica"""
        empleados = obj.empleados.all()  # Filtra empleados de esta tienda
        return [{"id": emp.id, "nombre": emp.usuario.username} for emp in empleados]

    def create(self, validated_data):
        """
        Sobrescribe el método create para asignar automáticamente el propietario de la tienda.
        """
        request = self.context.get('request')
        if request and hasattr(request, "user"):
            validated_data['propietario'] = request.user  # Asignar el usuario autenticado como propietario
        return Tienda.objects.create(**validated_data)
    
    
    def update(self, instance, validated_data):
        empleados = validated_data.pop('empleados', None)  # Se maneja aparte para evitar errores
        instance.nombre = validated_data.get('nombre', instance.nombre)
        instance.direccion = validated_data.get('direccion', instance.direccion)
        
        if empleados is not None:
            instance.empleados.set(empleados)  # Actualiza empleados

        instance.save()
        return instance

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
        fields = '__all__'

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

