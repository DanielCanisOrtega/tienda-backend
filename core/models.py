from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone


# Create your models here.

#  Usuario del sistema (Administrador o Vendedor)
class Usuario(AbstractUser):
    telefono = models.CharField(max_length=15, blank=True, null=True)
    # Evitar conflicto con 'groups' y 'user_permissions'
    groups = models.ManyToManyField(Group, related_name="usuarios", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="usuarios", blank=True)

    def __str__(self):
        return self.username

# Tienda (cada usuario puede administrar varias tiendas)
class Tienda(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.TextField()
    propietario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="tiendas")

    def __str__(self):
        return self.nombre

#  Empleados de la tienda (Solo vendedores)
class Empleado(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    tienda = models.ForeignKey(Tienda, on_delete=models.CASCADE, related_name="empleados")
    fecha_contratacion = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.tienda.nombre}"

#  Productos en el inventario de una tienda
class Producto(models.Model):
    tienda = models.ForeignKey(Tienda, on_delete=models.CASCADE, related_name="productos")
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=50)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.PositiveIntegerField()
    codigo_barras = models.CharField(max_length=50, unique=True, blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} ({self.tienda.nombre})"

#  Caja (Control de apertura y cierre por turno)
class Caja(models.Model):
    TURNO_CHOICES = [
        ('mañana', 'Mañana'),
        ('noche', 'Noche'),
    ]
    
    tienda = models.ForeignKey(Tienda, on_delete=models.CASCADE, related_name="cajas")
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="cajas_abiertas")
    turno = models.CharField(max_length=10, choices=TURNO_CHOICES, default='Mañana')  # Turno de la caja
    saldo_inicial = models.DecimalField(max_digits=10, decimal_places=2)
    saldo_final = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fecha_apertura = models.DateTimeField(default=timezone.now)
    fecha_cierre = models.DateTimeField(blank=True, null=True)
    estado = models.CharField(max_length=10, choices=[('abierta', 'Abierta'), ('cerrada', 'Cerrada')], default='abierta')

    def cerrar_caja(self, saldo_final):
        self.saldo_final = saldo_final
        self.fecha_cierre = timezone.now()
        self.estado = 'cerrada'
        self.save()

    def __str__(self):
        return f"Caja {self.id} - {self.tienda.nombre} - {self.turno} - {self.estado}"


#  Ventas (Asociadas a una caja abierta)
class Venta(models.Model):
    tienda = models.ForeignKey(Tienda, on_delete=models.CASCADE, related_name="ventas")
    caja = models.ForeignKey(Caja, on_delete=models.CASCADE, related_name="ventas")
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="ventas_realizadas")
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Venta {self.id} - {self.tienda.nombre} - ${self.total}"

#  Detalle de Venta (Productos vendidos)
class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

#  Gastos (Asociados a una caja abierta)
class Gasto(models.Model):
    tienda = models.ForeignKey(Tienda, on_delete=models.CASCADE, related_name="gastos")
    caja = models.ForeignKey(Caja, on_delete=models.CASCADE, related_name="gastos")
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="gastos_realizados")
    fecha = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.CharField(max_length=50)

    def __str__(self):
        return f"Gasto {self.id} - {self.tienda.nombre} - ${self.monto}"

#  Configuración de la tienda (ejemplo: activar/desactivar pedidos por voz)
class Configuracion(models.Model):
    tienda = models.OneToOneField(Tienda, on_delete=models.CASCADE, related_name="configuracion")
    pedidos_por_voz = models.BooleanField(default=False)
    stock_minimo_alerta = models.PositiveIntegerField(default=5)

    def __str__(self):
        return f"Configuración - {self.tienda.nombre}"
