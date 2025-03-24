from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CajaViewSet, UsuarioViewSet, TiendaViewSet, EmpleadoViewSet, ProductoViewSet, VentaViewSet,
    DetalleVentaViewSet, GastoViewSet
)

# Configuración del router para manejar los endpoints automáticamente
router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet)
router.register(r'tiendas', TiendaViewSet)
router.register(r'empleados', EmpleadoViewSet)
router.register(r'productos', ProductoViewSet, basename='producto')
router.register(r'ventas', VentaViewSet)
router.register(r'detalle-ventas', DetalleVentaViewSet)
router.register(r'gastos', GastoViewSet)
router.register(r'cajas', CajaViewSet, basename='caja')

urlpatterns = [
    path('', include(router.urls)),  # Incluir todas las rutas del router
]
