from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CajaViewSet, UsuarioViewSet, TiendaViewSet, EmpleadoViewSet, ProductoViewSet, VentaViewSet,
    DetalleVentaViewSet, GastoViewSet,PasswordResetSMSView
)

# Configuración del router para manejar los endpoints automáticamente
router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet)
router.register(r'tiendas', TiendaViewSet)
router.register(r'empleados', EmpleadoViewSet)
router.register(r'productos', ProductoViewSet, basename='producto')
router.register(r'ventas', VentaViewSet)
router.register(r'detalle-ventas', DetalleVentaViewSet)
router.register(r'gastos', GastoViewSet, basename='gasto')
router.register(r'cajas', CajaViewSet, basename='caja')

urlpatterns = [
    path('', include(router.urls)),  # Incluir todas las rutas del router
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    #path('auth/password-reset-sms/', PasswordResetSMSView.as_view(), name='password-reset-sms'),
]
