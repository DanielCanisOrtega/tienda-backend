from django.urls import path, include
from django.contrib.auth import views as auth_views
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
router.register(r'gastos', GastoViewSet, basename='gasto')
router.register(r'cajas', CajaViewSet, basename='caja')

urlpatterns = [
    path('', include(router.urls)),  # Incluir todas las rutas del router
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    path('reset_password/', auth_views.PasswordResetView.as_view(), name='password_reset'),  # Solicitar restablecimiento
    path('reset_password_send/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),  # Solicitar restablecimiento
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'), # Solicitar restablecimiento
]



