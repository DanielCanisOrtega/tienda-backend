from django.shortcuts import get_object_or_404
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Usuario, Tienda, Empleado, Producto, Venta, DetalleVenta, Gasto, Caja

# Obtener el modelo de usuario personalizado
#Usuario = get_user_model()

# Serializador para Usuario
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'telefono']

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        return token
    
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
    class Meta:
        model = Producto
        fields = ["id", "nombre", "categoria", "precio", "cantidad", "codigo_barras"]

    

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
    """
    Serializador para gestionar gastos.
    """

    class Meta:
        model = Gasto
        fields = ["id", "tienda", "caja", "usuario", "fecha", "descripcion", "monto", "categoria"]
        read_only_fields = ["id", "fecha", "usuario", "caja", "tienda"]  # La tienda se asignará automáticamente

    def validate(self, data):
        """
        Valida que haya una caja abierta en la tienda activa antes de registrar el gasto.
        """
        request = self.context.get("request")
        if not request:
            raise serializers.ValidationError("No se pudo obtener el usuario de la solicitud.")

        tienda_id = request.session.get("tienda_id")  # Obtener la tienda activa de la sesión
        if not tienda_id:
            raise serializers.ValidationError("No hay una tienda activa seleccionada.")

        tienda = get_object_or_404(Tienda, id=tienda_id)
        caja_abierta = Caja.objects.filter(tienda=tienda, estado="abierta").first()
        if not caja_abierta:
            raise serializers.ValidationError("No hay una caja abierta en la tienda para registrar el gasto.")

        data["usuario"] = request.user
        data["tienda"] = tienda  # Asigna automáticamente la tienda activa
        data["caja"] = caja_abierta
        return data


class CajaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caja
        fields = ['id', 'usuario', 'turno', 'saldo_inicial', 'saldo_final', 'fecha_apertura', 'fecha_cierre', 'estado']
        read_only_fields = ['id', 'usuario', 'fecha_apertura', 'fecha_cierre', 'estado']

    def validate(self, data):
        """
        Validar que no haya otra caja abierta en la tienda activa.
        """
        request = self.context.get('request')
        tienda_id = request.session.get("tienda_id")
        
        if not tienda_id:
            raise serializers.ValidationError("No hay una tienda activa seleccionada.")

        # Verificar si ya existe una caja abierta en la tienda activa
        if Caja.objects.filter(tienda_id=tienda_id, estado='abierta').exists():
            raise serializers.ValidationError("Ya hay una caja abierta en la tienda activa.")
        
        return data

    def create(self, validated_data):
        """
        Asigna la tienda activa y el usuario autenticado al crear la caja.
        """
        request = self.context.get('request')
        tienda_id = request.session.get("tienda_id")
        
        if not tienda_id:
            raise serializers.ValidationError("No hay una tienda activa seleccionada.")
        
        validated_data['tienda_id'] = tienda_id
        validated_data['usuario'] = request.user
        
        return super().create(validated_data)
