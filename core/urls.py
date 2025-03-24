from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    CajaViewSet,UserProfileView, UsuarioViewSet, TiendaViewSet, EmpleadoViewSet, ProductoViewSet, VentaViewSet,
    DetalleVentaViewSet, GastoViewSet
)

# Configuración del router para manejar los endpoints automáticamente
router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet)
router.register(r'tiendas', TiendaViewSet)
router.register(r'empleados', EmpleadoViewSet)
router.register(r'productos', ProductoViewSet)
router.register(r'ventas', VentaViewSet)
router.register(r'detalle-ventas', DetalleVentaViewSet)
router.register(r'gastos', GastoViewSet)
router.register(r'cajas', CajaViewSet, basename='caja')

urlpatterns = [
    # Endpoint para login (obtener access y refresh token)
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # Endpoint para refrescar el token
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Endpoint opcional para ver el perfil del usuario autenticado
    path('perfil/', UserProfileView.as_view(), name='user_profile'),
    path('', include(router.urls)),  # Incluir todas las rutas del router
]