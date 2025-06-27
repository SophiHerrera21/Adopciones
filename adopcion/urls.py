from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .decorators import admin_email_required

urlpatterns = [
    # Rutas principales
    path('', views.inicio, name='inicio'),
    path('lista-mascotas/', views.lista_mascotas, name='lista_mascotas'),
    path('mascota/<int:mascota_id>/', views.mascota_detalle, name='mascota_detalle'),
    path('quienes-somos/', views.quienes_somos_view, name='quienes_somos'),
    path('donar/', views.realizar_donacion_mejorado, name='donar'),
    
    # Rutas de Autenticación
    path('registro/', views.registro_view, name='registro'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='inicio'), name='logout'),
    
    # Rutas de Panel de Administración (Protegidas)
    path('panel/', admin_email_required(views.admin_dashboard), name='admin_dashboard'),
    path('panel/solicitudes/', admin_email_required(views.lista_solicitudes), name='admin_solicitudes'),
    path('panel/solicitud/<int:solicitud_id>/', admin_email_required(views.detalle_solicitud), name='detalle_solicitud'),
    path('panel/solicitud/<int:solicitud_id>/aprobar/', admin_email_required(views.aprobar_solicitud), name='aprobar_solicitud'),
    path('panel/solicitud/<int:solicitud_id>/rechazar/', admin_email_required(views.rechazar_solicitud), name='rechazar_solicitud'),
    path('panel/solicitud/<int:solicitud_id>/<str:nuevo_estado>/', admin_email_required(views.actualizar_estado_solicitud), name='actualizar_estado_solicitud'),
    path('panel/mascotas/', admin_email_required(views.admin_editar_mascotas), name='admin_editar_mascotas'),
    path('panel/agregar-mascota/', admin_email_required(views.agregar_mascota_mejorado), name='admin_agregar_mascota'),
    path('panel/reportes/', admin_email_required(views.pagina_reportes), name='admin_reportes'),
    path('panel/reportes/mascotas-pdf/', admin_email_required(views.generar_mascotas_pdf), name='generar_mascotas_pdf'),
    path('panel/reportes/donaciones-pdf/', admin_email_required(views.generar_donaciones_pdf), name='generar_donaciones_pdf'),
    path('panel/reportes/solicitudes-pdf/', admin_email_required(views.generar_solicitudes_pdf), name='generar_solicitudes_pdf'),
    path('panel/reportes/actividad-pdf/', admin_email_required(views.generar_actividad_pdf), name='generar_actividad_pdf'),
    path('panel/correo-masivo/', admin_email_required(views.enviar_correo_masivo_view), name='admin_correo_masivo'),
    path('panel/probar-correo/', admin_email_required(views.probar_correo_bienvenida), name='admin_probar_correo'),
    
    # Nuevas rutas para búsqueda de donantes y gestión de categorías
    path('panel/busqueda-donantes/', admin_email_required(views.busqueda_donantes), name='busqueda_donantes'),
    path('panel/busqueda-donaciones/', admin_email_required(views.busqueda_multiple_donaciones), name='busqueda_multiple_donaciones'),
    path('panel/busqueda-mascotas/', admin_email_required(views.busqueda_mascotas_avanzada), name='busqueda_mascotas_avanzada'),
    path('panel/gestionar-categorias/', admin_email_required(views.gestionar_categorias), name='gestionar_categorias'),
    path('panel/editar-categoria/<int:categoria_id>/', admin_email_required(views.editar_categoria), name='editar_categoria'),
    path('panel/eliminar-categoria/<int:categoria_id>/', admin_email_required(views.eliminar_categoria), name='eliminar_categoria'),
    
    # Rutas para seguimiento de mascotas
    path('panel/seguimiento-mascota/<int:mascota_id>/', admin_email_required(views.seguimiento_mascota), name='seguimiento_mascota'),
    path('panel/editar-mascota-mejorado/<int:mascota_id>/', admin_email_required(views.editar_mascota_mejorado), name='editar_mascota_mejorado'),

    # Rutas de Adopción
    path('mascota/<int:mascota_id>/solicitar/', views.solicitar_adopcion, name='solicitar_adopcion'),

    # Rutas para reportes (Administrador)
    path('perfil/', views.perfil_view, name='perfil'),
    path('perfil/mi-reporte-donaciones/', views.generar_mi_reporte_donaciones, name='mi_reporte_donaciones'),
    
    # Rutas de Favoritos
    path('favoritos/', views.mis_favoritos, name='mis_favoritos'),
    path('mascota/<int:mascota_id>/agregar-favorito/', views.agregar_favorito, name='agregar_favorito'),
    path('mascota/<int:mascota_id>/quitar-favorito/', views.quitar_favorito, name='quitar_favorito'),

    # Rutas de notificaciones
    path('notificaciones/', views.notificaciones, name='notificaciones'),
    path('notificaciones/marcar-leida/<int:notificacion_id>/', views.marcar_notificacion_leida, name='marcar_notificacion_leida'),
    path('notificaciones/ajax/', views.obtener_notificaciones_ajax, name='obtener_notificaciones_ajax'),

    # Rutas de password reset
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    # Alternativas bajo /accounts/ para compatibilidad
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset_alt'),
    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done_alt'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm_alt'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete_alt'),
    path('recuperar-password/', views.recuperar_password_email, name='recuperar_password_email'),
    path('recuperar-password/codigo/', views.recuperar_password_codigo, name='recuperar_password_codigo'),
    path('recuperar-password/nueva/', views.recuperar_password_nueva, name='recuperar_password_nueva'),
    path('admin/busqueda-multiple-donantes/', views.busqueda_multiple_donantes, name='busqueda_multiple_donantes'),
] 