from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .decorators import admin_email_required
from django.shortcuts import redirect
from django.views.generic import RedirectView

# Este es el router de la app, es llamado por el router del proyecto
urlpatterns = [
    # Rutas principales
    path('', views.inicio, name='inicio'),
    path('lista-mascotas/', views.lista_mascotas, name='lista_mascotas'),
    path('mascota/<int:mascota_id>/', views.mascota_detalle, name='mascota_detalle'),
    path('quienes-somos/', views.quienes_somos_view, name='quienes_somos'),
    path('donar/', views.realizar_donacion, name='donar'),
    
    # Rutas de Autenticación
    path('registro/', views.registro_view, name='registro'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='inicio'), name='logout'),
    
    # Rutas de Panel de Administración (Protegidas)
    path('panel/', admin_email_required(views.admin_dashboard), name='admin_dashboard'),
    path('panel/agregar-mascota/', admin_email_required(views.agregar_mascota), name='agregar_mascota'),
    path('panel/mascota/<int:mascota_id>/editar/', admin_email_required(views.editar_mascota), name='editar_mascota'),
    path('panel/solicitudes/', admin_email_required(views.lista_solicitudes), name='lista_solicitudes'),
    path('panel/solicitud/<int:solicitud_id>/', admin_email_required(views.detalle_solicitud), name='detalle_solicitud'),
    path('panel/solicitud/<int:solicitud_id>/actualizar/<str:nuevo_estado>/', admin_email_required(views.actualizar_estado_solicitud), name='actualizar_estado_solicitud'),
    path('panel/reportes/', admin_email_required(views.pagina_reportes), name='pagina_reportes'),
    path('panel/reportes/mascotas/', admin_email_required(views.generar_mascotas_pdf), name='pdf_mascotas'),
    path('panel/reportes/donaciones/', admin_email_required(views.generar_donaciones_pdf), name='pdf_donaciones'),
    path('panel/reportes/solicitudes/', admin_email_required(views.generar_solicitudes_pdf), name='pdf_solicitudes'),
    path('panel/reportes/actividad/', admin_email_required(views.generar_actividad_pdf), name='pdf_actividad'),
    path('panel/probar-correo/', admin_email_required(views.probar_correo_bienvenida), name='probar_correo'),
    path('panel/correo-masivo/', admin_email_required(views.enviar_correo_masivo_view), name='enviar_correo_masivo'),
    path('panel/mascotas/editar-masivo/', admin_email_required(views.admin_editar_mascotas), name='admin_editar_mascotas'),
    path('panel/seguimiento-mascotas/', admin_email_required(views.admin_seguimiento_mascotas), name='admin_seguimiento_mascotas'),

    # Rutas de Adopción
    path('mascota/<int:mascota_id>/solicitar/', views.solicitar_adopcion, name='solicitar_adopcion'),

    # Rutas para reportes (Administrador)
    # path('reportes/mascotas/fullpdf/', views.generar_mascotas_adoptadas_pdf, name='pdf_mascotas'),
    # path('reportes/donaciones/fullpdf/', views.generar_donaciones_pdf, name='pdf_donaciones'),
    # path('reportes/seguimientos/fullpdf/', views.generar_seguimientos_pdf, name='pdf_seguimientos'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('perfil/mi-reporte-donaciones/', views.generar_mi_reporte_donaciones, name='mi_reporte_donaciones'),
    
    # Rutas de Favoritos
    path('favoritos/', views.mis_favoritos, name='mis_favoritos'),
    path('mascota/<int:mascota_id>/agregar-favorito/', views.agregar_favorito, name='agregar_favorito'),
    path('mascota/<int:mascota_id>/quitar-favorito/', views.quitar_favorito, name='quitar_favorito'),

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
    path('admin/seguimiento/', RedirectView.as_view(url='/admin/seguimiento-mascotas/', permanent=True)),
    path('admin/seguimiento/<int:seguimiento_id>/aprobar/', views.aprobar_seguimiento, name='aprobar_seguimiento'),
    path('admin/seguimiento/<int:seguimiento_id>/denegar/', views.denegar_seguimiento, name='denegar_seguimiento'),
    path('admin/seguimiento/<int:seguimiento_id>/cambiar-fecha/', views.cambiar_fecha_seguimiento, name='cambiar_fecha_seguimiento'),
    path('admin/citas-pre-adopcion/', views.admin_citas_pre_adopcion, name='admin_citas_pre_adopcion'),
    path('admin/cita/<int:cita_id>/estado/<str:nuevo_estado>/', views.cambiar_estado_cita, name='cambiar_estado_cita'),
] 