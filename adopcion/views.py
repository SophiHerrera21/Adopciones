from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Mascota, SolicitudAdopcion, Donacion, Favorito, Usuario, PasswordResetCode
from .forms import SolicitudAdopcionForm, CustomUserCreationForm, UserUpdateForm, DonacionForm, MascotaAdminForm, ReporteMensualForm, PasswordResetEmailForm, PasswordResetCodeForm, PasswordResetNewPasswordForm
from .decorators import admin_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json
from calendar import month_name
import os
import random
from datetime import timedelta

def enviar_correo_bienvenida(usuario):
    """Envía un correo de bienvenida a un nuevo usuario."""
    subject = '¡Bienvenido/a a Luna & Lía!'
    context = {'usuario': usuario}
    html_message = render_to_string('emails/bienvenida.html', context)
    plain_message = render_to_string('emails/bienvenida.txt', context)
    
    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [usuario.email],
            html_message=html_message,
            fail_silently=False
        )
    except Exception as e:
        # En un caso real, aquí podrías registrar el error en un sistema de logs
        print(f"Error al enviar correo de bienvenida a {usuario.email}: {e}")

def registro_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            # Asignar rol de administrador si el email es del dominio correcto
            if usuario.email.endswith('@lunaylia.com'):
                usuario.rol = 'administrador'
                usuario.is_staff = True # Opcional: para que pueda acceder al admin de Django
            usuario.save()
            
            # Enviar correo de bienvenida
            enviar_correo_bienvenida(usuario)
            
            messages.success(request, '¡Registro exitoso! Ahora puedes iniciar sesión con tus credenciales.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/registro.html', {'form': form})

# Create your views here.

def inicio(request):
    # Obtener mascotas disponibles para el carrusel
    mascotas_disponibles = Mascota.objects.filter(estado_adopcion='disponible').order_by('-fecha_ingreso')[:6]
    
    # Contador de peludos en la fundación
    peludos_en_fundacion = Mascota.contar_peludos_en_fundacion()
    peludos_adoptados = Mascota.contar_peludos_adoptados()
    
    # Estadísticas generales
    total_mascotas = Mascota.objects.count()
    perros_disponibles = Mascota.objects.filter(tipo='perro', estado_adopcion='disponible').count()
    gatos_disponibles = Mascota.objects.filter(tipo='gato', estado_adopcion='disponible').count()
    
    context = {
        'mascotas_disponibles': mascotas_disponibles,
        'peludos_en_fundacion': peludos_en_fundacion,
        'peludos_adoptados': peludos_adoptados,
        'total_mascotas': total_mascotas,
        'perros_disponibles': perros_disponibles,
        'gatos_disponibles': gatos_disponibles,
    }
    return render(request, 'adopcion/inicio.html', context)

def quienes_somos_view(request):
    """
    Muestra la página con la misión, visión, objetivos y equipo de la fundación.
    """
    equipo = [
        {'nombre': 'Ana García', 'rol': 'Fundadora y Directora', 'foto': 'https://images.pexels.com/photos/774909/pexels-photo-774909.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1', 'descripcion': 'Apasionada por los animales desde niña, Ana fundó Luna & Lía con el sueño de no ver más animales sin hogar.'},
        {'nombre': 'Carlos Ruiz', 'rol': 'Coordinador de Adopciones', 'foto': 'https://images.pexels.com/photos/91227/pexels-photo-91227.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1', 'descripcion': 'Carlos se asegura de que cada peludo encuentre a la familia perfecta, guiando a los adoptantes en cada paso.'},
        {'nombre': 'María López', 'rol': 'Veterinaria Principal', 'foto': 'https://images.pexels.com/photos/1181690/pexels-photo-1181690.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1', 'descripcion': 'Con años de experiencia, María cuida de la salud de todos nuestros rescatados, asegurando su bienestar.'},
        {'nombre': 'Javier Torres', 'rol': 'Encargado de Voluntarios', 'foto': 'https://images.pexels.com/photos/1516680/pexels-photo-1516680.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1', 'descripcion': 'Javier organiza y motiva a nuestro increíble equipo de voluntarios, el corazón de nuestra fundación.'},
    ]
    context = {
        'equipo': equipo
    }
    return render(request, 'adopcion/quienes_somos.html', context)

@login_required
def solicitar_adopcion(request, mascota_id):
    mascota = get_object_or_404(Mascota, id=mascota_id, estado_adopcion='disponible')
    
    # Verificar si ya tiene una solicitud pendiente para esta mascota
    if SolicitudAdopcion.objects.filter(usuario=request.user, mascota=mascota, estado_solicitud='pendiente').exists():
        messages.warning(request, f'Ya tienes una solicitud pendiente para {mascota.nombre}.')
        return redirect('mascota_detalle', mascota_id=mascota.id)
    
    if request.method == 'POST':
        form = SolicitudAdopcionForm(request.POST)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.usuario = request.user
            solicitud.mascota = mascota
            solicitud.save()
            
            # Cambiar estado de la mascota a 'en_proceso'
            mascota.estado_adopcion = 'en_proceso'
            mascota.save()

            # Enviar notificación por email al usuario
            try:
                enviar_correo_solicitud_recibida(solicitud)
            except Exception as e:
                print(f"Error enviando email: {e}")

            # Enviar notificación a administradores
            try:
                enviar_correo_admin_nueva_solicitud(solicitud)
            except Exception as e:
                print(f"Error enviando email a admin: {e}")

            messages.success(request, f'¡Tu solicitud para adoptar a {mascota.nombre} ha sido enviada con éxito! Nos pondremos en contacto contigo pronto.')
            return redirect('perfil')
    else:
        form = SolicitudAdopcionForm()
        
    return render(request, 'adopcion/solicitud_adopcion.html', {
        'form': form,
        'mascota': mascota
    })

def enviar_correo_solicitud_recibida(solicitud):
    """Envía un email confirmando que se recibió la solicitud."""
    subject = f'Solicitud de adopción recibida - {solicitud.mascota.nombre}'
    context = {'solicitud': solicitud}
    html_message = render_to_string('emails/solicitud_recibida.html', context)
    plain_message = render_to_string('emails/solicitud_recibida.txt', context)
    send_mail(
        subject,
        plain_message,
        settings.EMAIL_HOST_USER,
        [solicitud.usuario.email],
        html_message=html_message,
        fail_silently=False
    )

def enviar_correo_admin_nueva_solicitud(solicitud):
    """Envía un email a los administradores sobre una nueva solicitud."""
    subject = f'Nueva solicitud de adopción - {solicitud.mascota.nombre}'
    context = {'solicitud': solicitud}
    html_message = render_to_string('emails/admin_nueva_solicitud.html', context)
    plain_message = render_to_string('emails/admin_nueva_solicitud.txt', context)
    
    # Enviar a todos los administradores
    admins = Usuario.objects.filter(rol='administrador')
    admin_emails = [admin.email for admin in admins]
    
    if admin_emails:
        send_mail(
            subject,
            plain_message,
            settings.EMAIL_HOST_USER,
            admin_emails,
            html_message=html_message,
            fail_silently=False
        )

@admin_required
def admin_dashboard(request):
    # Estadísticas generales
    total_mascotas = Mascota.objects.count()
    mascotas_disponibles = Mascota.objects.filter(estado_adopcion='disponible').count()
    mascotas_en_proceso = Mascota.objects.filter(estado_adopcion='en_proceso').count()
    mascotas_adoptadas = Mascota.objects.filter(estado_adopcion='adoptado').count()
    mascotas_en_tratamiento = Mascota.objects.filter(estado_adopcion='en_tratamiento').count()
    
    # Contador de peludos en la fundación
    peludos_en_fundacion = Mascota.contar_peludos_en_fundacion()
    peludos_adoptados = Mascota.contar_peludos_adoptados()
    
    solicitudes_pendientes = SolicitudAdopcion.objects.filter(estado_solicitud='pendiente').count()
    solicitudes_aprobadas = SolicitudAdopcion.objects.filter(estado_solicitud='aprobada').count()
    solicitudes_rechazadas = SolicitudAdopcion.objects.filter(estado_solicitud='rechazada').count()
    
    total_usuarios = Usuario.objects.count()
    total_donado = Donacion.objects.filter(tipo_donacion='monetaria').aggregate(total=Sum('monto'))['total'] or 0
    
    # Datos para gráficas de pastel
    # Gráfica de estado de mascotas
    mascotas_data = {
        'Disponibles': mascotas_disponibles,
        'En Proceso': mascotas_en_proceso,
        'Adoptadas': mascotas_adoptadas,
        'En Tratamiento': mascotas_en_tratamiento
    }
    
    # Gráfica de solicitudes de adopción
    solicitudes_data = {
        'Pendientes': solicitudes_pendientes,
        'Aprobadas': solicitudes_aprobadas,
        'Rechazadas': solicitudes_rechazadas
    }
    
    # Gráfica de donaciones por categoría
    donaciones_monetarias = Donacion.objects.filter(tipo_donacion='monetaria').count()
    donaciones_alimentos = Donacion.objects.filter(tipo_donacion='insumos', categoria_insumo='alimentos').count()
    donaciones_medicamentos = Donacion.objects.filter(tipo_donacion='insumos', categoria_insumo='medicamentos').count()
    donaciones_juguetes = Donacion.objects.filter(tipo_donacion='insumos', categoria_insumo='juguetes').count()
    donaciones_otros = Donacion.objects.filter(tipo_donacion='insumos').exclude(
        categoria_insumo__in=['alimentos', 'medicamentos', 'juguetes']
    ).count()
    
    donaciones_data = {
        'Monetarias': donaciones_monetarias,
        'Alimentos': donaciones_alimentos,
        'Medicamentos': donaciones_medicamentos,
        'Juguetes': donaciones_juguetes,
        'Otros': donaciones_otros
    }
    
    # Últimas actividades (tiempo real)
    ultimas_mascotas = Mascota.objects.order_by('-fecha_ingreso')[:5]
    ultimas_donaciones = Donacion.objects.order_by('-fecha_donacion')[:5]
    ultimas_solicitudes = SolicitudAdopcion.objects.order_by('-fecha_solicitud')[:5]

    context = {
        'total_mascotas': total_mascotas,
        'mascotas_disponibles': mascotas_disponibles,
        'mascotas_en_proceso': mascotas_en_proceso,
        'mascotas_adoptadas': mascotas_adoptadas,
        'mascotas_en_tratamiento': mascotas_en_tratamiento,
        'peludos_en_fundacion': peludos_en_fundacion,
        'peludos_adoptados': peludos_adoptados,
        'solicitudes_pendientes': solicitudes_pendientes,
        'solicitudes_aprobadas': solicitudes_aprobadas,
        'solicitudes_rechazadas': solicitudes_rechazadas,
        'total_usuarios': total_usuarios,
        'total_donado': total_donado,
        'mascotas_data': mascotas_data,
        'solicitudes_data': solicitudes_data,
        'donaciones_data': donaciones_data,
        'ultimas_mascotas': ultimas_mascotas,
        'ultimas_donaciones': ultimas_donaciones,
        'ultimas_solicitudes': ultimas_solicitudes,
        'mascotas_data_json': json.dumps(mascotas_data),
        'solicitudes_data_json': json.dumps(solicitudes_data),
        'donaciones_data_json': json.dumps(donaciones_data),
    }
    return render(request, 'adopcion/admin_dashboard.html', context)

@admin_required
def lista_solicitudes(request):
    solicitudes = SolicitudAdopcion.objects.select_related('usuario', 'mascota').order_by('-fecha_solicitud')
    context = {
        'solicitudes': solicitudes
    }
    return render(request, 'adopcion/lista_solicitudes.html', context)

@admin_required
def detalle_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(SolicitudAdopcion, id=solicitud_id)
    context = {
        'solicitud': solicitud
    }
    return render(request, 'adopcion/detalle_solicitud.html', context)

def enviar_correo_estado_solicitud(solicitud):
    """Envía un email notificando el cambio de estado de una solicitud."""
    subject = f'Actualización sobre tu solicitud para adoptar a {solicitud.mascota.nombre}'
    context = {'solicitud': solicitud}
    html_message = render_to_string('emails/estado_solicitud.html', context)
    plain_message = render_to_string('emails/estado_solicitud.txt', context)
    send_mail(
        subject,
        plain_message,
        settings.EMAIL_HOST_USER,
        [solicitud.usuario.email],
        html_message=html_message,
        fail_silently=False
    )

@admin_required
def actualizar_estado_solicitud(request, solicitud_id, nuevo_estado):
    if request.method == 'POST':
        solicitud = get_object_or_404(SolicitudAdopcion, id=solicitud_id)
        
        if nuevo_estado in ['aprobada', 'rechazada']:
            solicitud.estado_solicitud = nuevo_estado
            solicitud.fecha_respuesta = timezone.now()
            solicitud.id_admin_revisor = request.user
            solicitud.save()

            # Si se aprueba, actualizar la mascota
            if nuevo_estado == 'aprobada':
                mascota = solicitud.mascota
                mascota.estado_adopcion = 'adoptado'
                mascota.fecha_adopcion = timezone.now().date()
                mascota.save()
                # Rechazar otras solicitudes para la misma mascota
                SolicitudAdopcion.objects.filter(mascota=mascota).exclude(id=solicitud_id).update(
                    estado_solicitud='rechazada',
                    fecha_respuesta=timezone.now(),
                    id_admin_revisor=request.user
                )

            # Enviar email de notificación al usuario
            try:
                enviar_correo_estado_solicitud(solicitud)
                messages.success(request, f"La solicitud para {solicitud.mascota.nombre} ha sido {nuevo_estado} y el usuario ha sido notificado por email.")
            except Exception as e:
                messages.warning(request, f"La solicitud ha sido {nuevo_estado} pero hubo un error enviando el email: {e}")
        else:
            messages.error(request, "Estado no válido.")
        
        return redirect('detalle_solicitud', solicitud_id=solicitud.id)
    return redirect('inicio')

@admin_required
def pagina_reportes(request):
    """Muestra la página con los enlaces para generar los diferentes reportes PDF."""
    form = ReporteMensualForm()
    return render(request, 'adopcion/reportes.html', {'form': form})

@admin_required
def generar_mascotas_pdf(request):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Título con logo
    title_style = styles['Title']
    title_style.textColor = colors.HexColor("#8c6239")
    elements.append(Paragraph("Luna & Lía: Rescatando Huellas", title_style))
    elements.append(Paragraph("Reporte de Mascotas", styles['Heading1']))
    elements.append(Paragraph(f"Fecha del reporte: {timezone.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Estadísticas generales
    total_mascotas = Mascota.objects.count()
    disponibles = Mascota.objects.filter(estado_adopcion='disponible').count()
    en_proceso = Mascota.objects.filter(estado_adopcion='en_proceso').count()
    adoptadas = Mascota.objects.filter(estado_adopcion='adoptado').count()
    
    stats_data = [
        ["Total de Mascotas", str(total_mascotas)],
        ["Disponibles", str(disponibles)],
        ["En Proceso", str(en_proceso)],
        ["Adoptadas", str(adoptadas)]
    ]
    
    stats_table = Table(stats_data, colWidths=[200, 100])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#8c6239")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 20))

    # Tabla de mascotas
    elements.append(Paragraph("Lista de Mascotas", styles['Heading2']))
    mascotas = Mascota.objects.all().order_by('estado_adopcion', 'nombre')
    data = [["Nombre", "Tipo", "Raza", "Estado", "Fecha de Ingreso"]]
    
    for m in mascotas:
        estado_color = {
            'disponible': 'green',
            'en_proceso': 'orange',
            'adoptado': 'grey',
            'no_disponible': 'red'
        }.get(m.estado_adopcion, 'black')
        
        data.append([
            m.nombre, 
            m.get_tipo_display(), 
            m.raza or "Mestizo", 
            m.get_estado_adopcion_display(), 
            m.fecha_ingreso.strftime("%d/%m/%Y")
        ])
    
    tbl = Table(data, colWidths=[100, 80, 100, 100, 100])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#8c6239")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    elements.append(tbl)
    
    doc.build(elements)
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

@admin_required
def generar_donaciones_pdf(request):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=inch/2, leftMargin=inch/2, topMargin=inch/2, bottomMargin=inch/2)
    elements = []
    styles = getSampleStyleSheet()
    
    # Título con logo
    title_style = styles['Title']
    title_style.textColor = colors.HexColor("#8c6239")
    elements.append(Paragraph("Luna & Lía: Rescatando Huellas", title_style))

    # Filtros por mes y año
    mes = request.GET.get('mes')
    año = request.GET.get('año')
    
    donaciones_query = Donacion.objects.all()
    
    if mes and año:
        try:
            mes = int(mes)
            año = int(año)
            donaciones_query = donaciones_query.filter(
                fecha_donacion__year=año,
                fecha_donacion__month=mes
            )
            # Título del reporte dinámico
            nombre_mes = month_name[mes]
            report_title = f"Reporte de Donaciones - {nombre_mes} {año}"
        except (ValueError, IndexError):
            report_title = "Reporte de Donaciones (General)"
    else:
        report_title = "Reporte de Donaciones (General)"

    elements.append(Paragraph(report_title, styles['Heading1']))
    elements.append(Paragraph(f"Fecha del reporte: {timezone.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Estadísticas generales (basadas en el query)
    total_donaciones = donaciones_query.count()
    donaciones_monetarias = donaciones_query.filter(tipo_donacion='monetaria').count()
    donaciones_insumos = donaciones_query.filter(tipo_donacion='insumos').count()
    total_monetario = donaciones_query.filter(tipo_donacion='monetaria').aggregate(Sum('monto'))['monto__sum'] or 0
    
    stats_data = [
        ["Total de Donaciones", str(total_donaciones)],
        ["Donaciones Monetarias", str(donaciones_monetarias)],
        ["Donaciones de Insumos", str(donaciones_insumos)],
        ["Total Recaudado", f"${total_monetario:,.2f}"]
    ]
    
    stats_table = Table(stats_data, colWidths=[200, 100])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#8c6239")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 20))

    # Tabla de donaciones monetarias
    elements.append(Paragraph("Donaciones Monetarias", styles['Heading2']))
    donaciones_m = donaciones_query.filter(tipo_donacion='monetaria').order_by('-fecha_donacion')
    data_m = [["Donante", "Email", "Monto", "Medio de Pago", "Fecha"]]
    
    for d in donaciones_m:
        data_m.append([
            f"{d.nombre_donante} {d.apellido_donante}", 
            d.email_donante, 
            f"${d.monto:,.2f}", 
            d.get_medio_pago_display(), 
            d.fecha_donacion.strftime("%d/%m/%Y")
        ])
    
    if len(data_m) > 1:  # Si hay donaciones
        data_m.append(["TOTAL", "", f"${total_monetario:,.2f}", "", ""])
    
    tbl_m = Table(data_m)
    tbl_m.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#8c6239")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (-1, -1), (-1, -1), colors.HexColor("#d38d44")),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
    ]))
    elements.append(tbl_m)
    elements.append(Spacer(1, 20))

    # Tabla de donaciones de insumos
    elements.append(Paragraph("Donaciones de Insumos", styles['Heading2']))
    donaciones_i = donaciones_query.filter(tipo_donacion='insumos').order_by('-fecha_donacion')
    data_i = [["Donante", "Email", "Categoría", "Descripción", "Fecha"]]
    
    for d in donaciones_i:
        data_i.append([
            f"{d.nombre_donante} {d.apellido_donante}", 
            d.email_donante, 
            d.get_categoria_insumo_display(), 
            d.descripcion_insumo[:50] + "..." if len(d.descripcion_insumo) > 50 else d.descripcion_insumo,
            d.fecha_donacion.strftime("%d/%m/%Y")
        ])
    
    if len(data_i) > 1:  # Si hay donaciones
        tbl_i = Table(data_i)
        tbl_i.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#8c6239")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elements.append(tbl_i)
    else:
        elements.append(Paragraph("No hay donaciones de insumos registradas.", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

@login_required
def perfil_view(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Tu perfil ha sido actualizado con éxito!')
            return redirect('perfil')
    else:
        form = UserUpdateForm(instance=request.user)

    # Obtenemos las solicitudes del usuario
    solicitudes = SolicitudAdopcion.objects.filter(usuario=request.user).order_by('-fecha_solicitud')

    # Obtenemos las donaciones del usuario
    donaciones = Donacion.objects.filter(usuario=request.user).order_by('-fecha_donacion')

    context = {
        'form': form,
        'solicitudes': solicitudes,
        'donaciones': donaciones
    }
    return render(request, 'adopcion/perfil.html', context)

def enviar_correo_donacion(donacion):
    """Envía un email de agradecimiento por la donación."""
    subject = '¡Muchas gracias por tu generosa donación!'
    context = {'donacion': donacion}
    html_message = render_to_string('emails/donacion_gracias.html', context)
    plain_message = render_to_string('emails/donacion_gracias.txt', context)
    send_mail(subject, plain_message, settings.EMAIL_HOST_USER, [donacion.email_donante], html_message=html_message)

def mascota_detalle(request, mascota_id):
    """
    Muestra la página con toda la información detallada de una sola mascota.
    """
    mascota = get_object_or_404(Mascota, id=mascota_id)
    
    # Verificar si la mascota está en favoritos del usuario (si está autenticado)
    es_favorito = False
    if request.user.is_authenticated:
        es_favorito = Favorito.objects.filter(usuario=request.user, mascota=mascota).exists()
    
    context = {
        'mascota': mascota,
        'es_favorito': es_favorito
    }
    return render(request, 'adopcion/mascota_detalle.html', context)

def realizar_donacion(request):
    if request.method == 'POST':
        form = DonacionForm(request.POST)
        if form.is_valid():
            donacion = form.save(commit=False)
            if request.user.is_authenticated:
                donacion.usuario = request.user
            donacion.save()
            
            enviar_correo_donacion(donacion)
            
            messages.success(request, '¡Muchas gracias! Tu donación ha sido registrada. Hemos enviado un comprobante a tu correo.')
            return redirect('inicio')
    else:
        form = DonacionForm()

    return render(request, 'adopcion/donacion_form.html', {'form': form})

# Vistas para el sistema de favoritos
@login_required
@require_POST
def agregar_favorito(request, mascota_id):
    """Agrega una mascota a los favoritos del usuario."""
    mascota = get_object_or_404(Mascota, id=mascota_id)
    favorito, created = Favorito.objects.get_or_create(
        usuario=request.user,
        mascota=mascota
    )
    
    if created:
        return JsonResponse({'status': 'ok', 'message': f'{mascota.nombre} añadido a tus favoritos.'})
    else:
        return JsonResponse({'status': 'exist', 'message': f'{mascota.nombre} ya estaba en tus favoritos.'})

@login_required
@require_POST
def quitar_favorito(request, mascota_id):
    """Quita una mascota de los favoritos del usuario."""
    mascota = get_object_or_404(Mascota, id=mascota_id)
    try:
        favorito = Favorito.objects.get(usuario=request.user, mascota=mascota)
        favorito.delete()
        return JsonResponse({'status': 'ok', 'message': f'{mascota.nombre} ha sido removido de tus favoritos.'})
    except Favorito.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Favorito no encontrado.'})

@login_required
def mis_favoritos(request):
    """Muestra la lista de mascotas favoritas del usuario con filtros."""
    # Obtener parámetros de filtro
    tipo_filter = request.GET.get('tipo', '')
    edad_filter = request.GET.get('edad', '')
    estado_filter = request.GET.get('estado', '')
    
    # Obtener favoritos del usuario
    favoritos = Favorito.objects.filter(usuario=request.user).select_related('mascota')
    mascotas_favoritas = [favorito.mascota for favorito in favoritos]
    
    # Aplicar filtros
    if tipo_filter:
        mascotas_favoritas = [m for m in mascotas_favoritas if m.tipo == tipo_filter]
    
    if edad_filter:
        if edad_filter == '2-12':
            mascotas_favoritas = [m for m in mascotas_favoritas if 2 <= m.edad_aproximada <= 12]
        elif edad_filter == '1-2':
            mascotas_favoritas = [m for m in mascotas_favoritas if 12 <= m.edad_aproximada <= 24]
        elif edad_filter == '2-4':
            mascotas_favoritas = [m for m in mascotas_favoritas if 24 <= m.edad_aproximada <= 48]
        elif edad_filter == '5+':
            mascotas_favoritas = [m for m in mascotas_favoritas if m.edad_aproximada >= 60]
    
    if estado_filter:
        mascotas_favoritas = [m for m in mascotas_favoritas if m.estado_adopcion == estado_filter]
    
    context = {
        'mascotas': mascotas_favoritas,
        'es_pagina_favoritos': True,
        'filtros_activos': {
            'tipo': tipo_filter,
            'edad': edad_filter,
            'estado': estado_filter
        }
    }
    return render(request, 'adopcion/mis_favoritos.html', context)

@admin_required
def probar_correo_bienvenida(request):
    """
    Vista para que un admin pueda enviarse a sí mismo un correo de bienvenida de prueba.
    """
    usuario_actual = request.user
    
    try:
        enviar_correo_bienvenida(usuario_actual)
        messages.success(request, f'¡Correo de prueba enviado con éxito a {usuario_actual.email}!')
    except Exception as e:
        messages.error(request, f'Error al enviar el correo de prueba: {e}')
        
    return redirect('admin_dashboard')

def enviar_correo_masivo(asunto, mensaje_html, mensaje_texto, destinatarios):
    """Función para enviar correos masivos"""
    try:
        send_mail(
            asunto,
            mensaje_texto,
            settings.DEFAULT_FROM_EMAIL,
            destinatarios,
            html_message=mensaje_html,
            fail_silently=False,
        )
        return True, "Correos enviados exitosamente"
    except Exception as e:
        return False, f"Error enviando correos: {str(e)}"

@admin_required
def enviar_correo_masivo_view(request):
    """Vista para enviar correos masivos"""
    if request.method == 'POST':
        asunto = request.POST.get('asunto', '')
        mensaje = request.POST.get('mensaje', '')
        tipo_destinatarios = request.POST.get('tipo_destinatarios', 'todos')
        
        if not asunto or not mensaje:
            messages.error(request, 'Por favor completa todos los campos.')
            return redirect('enviar_correo_masivo')
        
        # Obtener destinatarios según el tipo
        if tipo_destinatarios == 'usuarios':
            destinatarios = list(Usuario.objects.filter(rol='usuario').values_list('email', flat=True))
        elif tipo_destinatarios == 'administradores':
            destinatarios = list(Usuario.objects.filter(rol='administrador').values_list('email', flat=True))
        else:  # todos
            destinatarios = list(Usuario.objects.values_list('email', flat=True))
        
        if not destinatarios:
            messages.warning(request, 'No hay destinatarios para enviar el correo.')
            return redirect('enviar_correo_masivo')
        
        # Crear mensaje HTML
        mensaje_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #8c6239, #d38d44); color: white; padding: 20px; text-align: center;">
                <h2>Luna & Lía: Rescatando Huellas</h2>
            </div>
            <div style="padding: 20px; background: #f9f9f9;">
                <p>{mensaje}</p>
                <hr style="border: 1px solid #ddd; margin: 20px 0;">
                <p style="font-size: 12px; color: #666;">
                    Este correo fue enviado desde el sistema de Luna & Lía.<br>
                    Si tienes alguna pregunta, contáctanos.
                </p>
            </div>
        </div>
        """
        
        # Enviar correos
        success, message = enviar_correo_masivo(asunto, mensaje_html, mensaje, destinatarios)
        
        if success:
            messages.success(request, f'Correo enviado exitosamente a {len(destinatarios)} destinatarios.')
        else:
            messages.error(request, message)
        
        return redirect('admin_dashboard')
    
    return render(request, 'adopcion/enviar_correo_masivo.html')

@admin_required
def generar_solicitudes_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    
    styles = getSampleStyleSheet()
    story = []
    
    # Filtros por mes y año
    mes = request.GET.get('mes')
    año = request.GET.get('año')
    
    solicitudes_query = SolicitudAdopcion.objects.all()
    
    if mes and año:
        try:
            mes = int(mes)
            año = int(año)
            solicitudes_query = solicitudes_query.filter(
                fecha_solicitud__year=año,
                fecha_solicitud__month=mes
            )
            # Título del reporte dinámico
            nombre_mes = month_name[mes]
            report_title = f"Reporte de Solicitudes - {nombre_mes} {año}"
            response['Content-Disposition'] = f'attachment; filename="reporte_solicitudes_{año}_{mes}.pdf"'
        except (ValueError, IndexError):
            report_title = "Reporte Detallado de Solicitudes de Adopción"
            response['Content-Disposition'] = f'attachment; filename="reporte_solicitudes_general.pdf"'
    else:
        report_title = "Reporte Detallado de Solicitudes de Adopción"
        response['Content-Disposition'] = f'attachment; filename="reporte_solicitudes_general.pdf"'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)

    # Título
    story.append(Paragraph(report_title, styles['h1']))
    story.append(Spacer(1, 0.2 * inch))

    # Estadísticas
    solicitudes = solicitudes_query
    total_solicitudes = solicitudes.count()
    stats = solicitudes.values('estado_solicitud').annotate(count=Count('estado_solicitud'))
    
    stats_data = [['Estado', 'Cantidad']]
    stats_dict = {}
    for stat in stats:
        stats_data.append([stat['estado_solicitud'].replace('_', ' ').title(), stat['count']])
        stats_dict[stat['estado_solicitud'].replace('_', ' ').title()] = stat['count']
    
    # Gráfico de Pastel
    if stats_dict:
        plt.figure(figsize=(5, 3))
        plt.pie(stats_dict.values(), labels=stats_dict.keys(), autopct='%1.1f%%', startangle=90)
        plt.title("Distribución de Solicitudes")
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight')
        img_buffer.seek(0)
        
        img = Image(img_buffer, width=3*inch, height=2*inch)
        img.hAlign = 'CENTER'
        story.append(img)
        plt.close()

    story.append(Spacer(1, 0.2 * inch))

    # Tabla de Resumen
    story.append(Paragraph("Resumen de Solicitudes", styles['h2']))
    
    stats_table = Table(stats_data)
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 0.3 * inch))

    # Lista detallada
    story.append(Paragraph("Detalle de Solicitudes", styles['h2']))
    solicitudes_list_data = [['ID', 'Mascota', 'Solicitante', 'Estado', 'Fecha']]
    for s in solicitudes:
        solicitudes_list_data.append([
            s.id,
            Paragraph(s.mascota.nombre, styles['Normal']),
            Paragraph(s.usuario.get_full_name(), styles['Normal']),
            s.get_estado_solicitud_display(),
            s.fecha_solicitud.strftime("%Y-%m-%d")
        ])

    sol_table = Table(solicitudes_list_data, colWidths=[0.5*inch, 1.5*inch, 2*inch, 1.5*inch, 1.5*inch])
    sol_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    story.append(sol_table)

    doc.build(story)
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response

@admin_required
def generar_actividad_pdf(request):
    """Genera un reporte de actividad reciente con timestamps."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Título con logo
    title_style = styles['Title']
    title_style.textColor = colors.HexColor("#8c6239")
    elements.append(Paragraph("Luna & Lía: Rescatando Huellas", title_style))
    elements.append(Paragraph("Reporte de Actividad Reciente", styles['Heading1']))
    elements.append(Paragraph(f"Fecha del reporte: {timezone.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Últimas mascotas ingresadas
    elements.append(Paragraph("Últimas Mascotas Ingresadas", styles['Heading2']))
    ultimas_mascotas = Mascota.objects.order_by('-fecha_ingreso')[:10]
    data_mascotas = [["Nombre", "Tipo", "Estado", "Fecha de Ingreso"]]
    
    for m in ultimas_mascotas:
        data_mascotas.append([
            m.nombre,
            m.get_tipo_display(),
            m.get_estado_adopcion_display(),
            m.fecha_ingreso.strftime("%d/%m/%Y %H:%M")
        ])
    
    tbl_mascotas = Table(data_mascotas, colWidths=[100, 80, 100, 120])
    tbl_mascotas.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#8c6239")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    elements.append(tbl_mascotas)
    elements.append(Spacer(1, 20))

    # Últimas donaciones
    elements.append(Paragraph("Últimas Donaciones", styles['Heading2']))
    ultimas_donaciones = Donacion.objects.order_by('-fecha_donacion')[:10]
    data_donaciones = [["Donante", "Tipo", "Detalle", "Fecha"]]
    
    for d in ultimas_donaciones:
        if d.tipo_donacion == 'monetaria':
            detalle = f"${d.monto:,.2f} - {d.get_medio_pago_display()}"
        else:
            detalle = f"{d.get_categoria_insumo_display()} - {d.descripcion_insumo[:30]}..."
        
        data_donaciones.append([
            f"{d.nombre_donante} {d.apellido_donante}",
            d.get_tipo_donacion_display(),
            detalle,
            d.fecha_donacion.strftime("%d/%m/%Y %H:%M")
        ])
    
    tbl_donaciones = Table(data_donaciones, colWidths=[120, 80, 150, 100])
    tbl_donaciones.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#8c6239")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
    ]))
    elements.append(tbl_donaciones)
    
    doc.build(elements)
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

@login_required
def generar_mi_reporte_donaciones(request):
    from calendar import month_name
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Título con logo
    title_style = styles['Title']
    title_style.textColor = colors.HexColor("#8c6239")
    # Logo
    logo_path = os.path.join(settings.STATIC_ROOT, 'images', 'logo.png')
    if os.path.exists(logo_path):
        elements.append(Image(logo_path, width=80, height=80))
    elements.append(Paragraph("Luna & Lía: Rescatando Huellas", title_style))

    # Filtros por mes y año
    mes = request.GET.get('mes')
    año = request.GET.get('año')
    donaciones_usuario = Donacion.objects.filter(usuario=request.user)
    if not donaciones_usuario.exists():
        donaciones_usuario = Donacion.objects.filter(email_donante=request.user.email)
    periodo = ""
    if mes and año:
        try:
            mes = int(mes)
            año = int(año)
            donaciones_usuario = donaciones_usuario.filter(fecha_donacion__year=año, fecha_donacion__month=mes)
            periodo = f" - {month_name[mes]} {año}"
        except Exception:
            pass
    elements.append(Paragraph(f"Mi Reporte de Donaciones{periodo}", styles['Heading1']))
    elements.append(Paragraph(f"Generado para: {request.user.nombre} {request.user.apellido}", styles['Normal']))
    elements.append(Paragraph(f"Fecha del reporte: {timezone.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 20))

    if not donaciones_usuario.exists():
        elements.append(Paragraph("No tienes donaciones registradas en este período.", styles['Normal']))
    else:
        # Estadísticas personales
        total_donaciones = donaciones_usuario.count()
        donaciones_monetarias = donaciones_usuario.filter(tipo_donacion='monetaria').count()
        donaciones_insumos = donaciones_usuario.filter(tipo_donacion='insumos').count()
        total_monetario = donaciones_usuario.filter(tipo_donacion='monetaria').aggregate(Sum('monto'))['monto__sum'] or 0
        stats_data = [
            ["Total de Donaciones", str(total_donaciones)],
            ["Donaciones Monetarias", str(donaciones_monetarias)],
            ["Donaciones de Insumos", str(donaciones_insumos)],
            ["Total Donado", f"${total_monetario:,.2f}"]
        ]
        stats_table = Table(stats_data, colWidths=[200, 100])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#8c6239")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 20))

        # Tabla tipo factura
        elements.append(Paragraph("Detalle de Donaciones", styles['Heading2']))
        data = [["Fecha", "Tipo", "Detalle", "Monto/Categoría", "Medio de Pago"]]
        for d in donaciones_usuario.order_by('-fecha_donacion'):
            if d.tipo_donacion == 'monetaria':
                detalle = f"${d.monto:,.2f}"
                medio = d.get_medio_pago_display()
                categoria = "-"
            else:
                detalle = d.get_categoria_insumo_display()
                medio = "-"
                categoria = d.descripcion_insumo[:50] + "..." if d.descripcion_insumo and len(d.descripcion_insumo) > 50 else d.descripcion_insumo
            data.append([
                d.fecha_donacion.strftime("%d/%m/%Y %H:%M"),
                d.get_tipo_donacion_display(),
                detalle,
                categoria if categoria else "-",
                medio
            ])
        tbl = Table(data, colWidths=[80, 60, 80, 150, 80])
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#8c6239")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(tbl)
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("¡Gracias por tu apoyo!", styles['Heading2']))
        elements.append(Paragraph("Cada donación hace posible que continuemos rescatando y cuidando a más mascotas que necesitan un hogar.", styles['Normal']))
    doc.build(elements)
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

@admin_required
def agregar_mascota(request):
    """Vista para que el administrador añada mascotas con imágenes adaptadas"""
    if request.method == 'POST':
        form = MascotaAdminForm(request.POST, request.FILES)
        if form.is_valid():
            mascota = form.save(commit=False)
            mascota.id_admin_registro = request.user
            mascota.fecha_registro = timezone.now()
            
            # Si no se especificó fecha de ingreso, usar la fecha actual
            if not mascota.fecha_ingreso:
                mascota.fecha_ingreso = timezone.now().date()
            
            mascota.save()
            
            # Mensaje de éxito
            messages.success(request, f'¡{mascota.nombre} ha sido registrado exitosamente en la fundación!')
            return redirect('admin_dashboard')
    else:
        form = MascotaAdminForm()
    
    context = {
        'form': form,
        'peludos_en_fundacion': Mascota.contar_peludos_en_fundacion(),
        'peludos_adoptados': Mascota.contar_peludos_adoptados(),
    }
    return render(request, 'adopcion/agregar_mascota.html', context)

@admin_required
def editar_mascota(request, mascota_id):
    mascota = get_object_or_404(Mascota, id=mascota_id)
    if request.method == 'POST':
        form = MascotaAdminForm(request.POST, request.FILES, instance=mascota)
        if form.is_valid():
            form.save()
            messages.success(request, f'Los datos de {mascota.nombre} han sido actualizados.')
            return redirect('admin_dashboard')
    else:
        form = MascotaAdminForm(instance=mascota)
    
    return render(request, 'adopcion/agregar_mascota.html', {
        'form': form,
        'titulo': f'Editar a {mascota.nombre}'
    })

def lista_mascotas(request):
    mascotas_list = Mascota.objects.all().order_by('-fecha_ingreso')
    
    # Obtener valores únicos para los filtros desde la base de datos
    tipos = Mascota.objects.values_list('tipo', flat=True).distinct()
    sexos = Mascota.objects.values_list('sexo', flat=True).distinct()
    tamaños = Mascota.objects.values_list('tamaño', flat=True).distinct()
    
    # Filtrado
    query = request.GET.get('q')
    tipo_filter = request.GET.get('tipo')
    sexo_filter = request.GET.get('sexo')
    tamaño_filter = request.GET.get('tamaño')
    estado_filter = request.GET.get('estado_adopcion')
    edad_min_filter = request.GET.get('edad_min')
    edad_max_filter = request.GET.get('edad_max')

    if query:
        mascotas_list = mascotas_list.filter(
            Q(nombre__icontains=query) |
            Q(raza__icontains=query) |
            Q(descripcion__icontains=query) |
            Q(personalidad__icontains=query)
        )
    if tipo_filter:
        mascotas_list = mascotas_list.filter(tipo=tipo_filter)
    if sexo_filter:
        mascotas_list = mascotas_list.filter(sexo=sexo_filter)
    if tamaño_filter:
        mascotas_list = mascotas_list.filter(tamaño=tamaño_filter)
    if estado_filter:
        mascotas_list = mascotas_list.filter(estado_adopcion=estado_filter)
    if edad_min_filter:
        mascotas_list = mascotas_list.filter(edad_aproximada__gte=edad_min_filter)
    if edad_max_filter:
        mascotas_list = mascotas_list.filter(edad_aproximada__lte=edad_max_filter)

    # Paginación
    paginator = Paginator(mascotas_list, 12)  # 12 mascotas por página
    page = request.GET.get('page')
    try:
        mascotas = paginator.page(page)
    except PageNotAnInteger:
        mascotas = paginator.page(1)
    except EmptyPage:
        mascotas = paginator.page(paginator.num_pages)
        
    total_results = mascotas_list.count()
    
    # Si la petición es AJAX, devolver solo el fragmento de la lista
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'adopcion/_lista_mascotas_parcial.html', {
            'mascotas': mascotas,
            'total_results': total_results
        })

    # Para la carga inicial de la página
    mascotas_carousel = Mascota.objects.filter(
        estado_adopcion='disponible', 
        imagen_principal__isnull=False
    ).exclude(imagen_principal='').order_by('?')[:5]

    context = {
        'mascotas': mascotas,
        'total_results': total_results,
        'tipos': Mascota.TIPO_CHOICES,
        'sexos': Mascota.SEXO_CHOICES,
        'tamaños': Mascota.TAMAÑO_CHOICES,
        'estados': Mascota.ESTADO_ADOPCION_CHOICES,
        'mascotas_carousel': mascotas_carousel,
        'page_obj': mascotas, # Para la paginación
        'is_paginated': mascotas.has_other_pages(),
        'filtros_actuales': request.GET, # Pasa todos los filtros GET a la plantilla
    }
    
    return render(request, 'adopcion/lista_mascotas.html', context)

@admin_required
@require_http_methods(["GET", "POST"])
def admin_editar_mascotas(request):
    from .models import Mascota
    if request.method == "POST":
        # Procesar edición masiva
        for key, value in request.POST.items():
            if key.startswith("nombre_"):
                mascota_id = key.split("_")[1]
                try:
                    mascota = Mascota.objects.get(id=mascota_id)
                    mascota.nombre = value
                    mascota.edad_aproximada = request.POST.get(f"edad_{mascota_id}")
                    mascota.estado_adopcion = request.POST.get(f"estado_{mascota_id}")
                    mascota.peso = request.POST.get(f"peso_{mascota_id}")
                    mascota.tipo = request.POST.get(f"tipo_{mascota_id}")
                    mascota.save()
                except Mascota.DoesNotExist:
                    continue
        return redirect('admin_editar_mascotas')
    mascotas = Mascota.objects.all().order_by('-fecha_ingreso')
    return render(request, 'adopcion/editar_mascotas_admin.html', {'mascotas': mascotas})

# Vista 1: Solicitar email para recuperación

def recuperar_password_email(request):
    if request.method == 'POST':
        form = PasswordResetEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower().strip()
            try:
                usuario = Usuario.objects.get(email=email)
            except Usuario.DoesNotExist:
                messages.error(request, 'No existe un usuario registrado con ese correo.')
                return render(request, 'registration/otp_password_reset_email.html', {'form': form})
            # Generar código
            codigo = f"{random.randint(100000, 999999)}"
            expiracion = timezone.now() + timedelta(minutes=10)
            PasswordResetCode.objects.filter(usuario=usuario, usado=False).update(usado=True)
            reset_code = PasswordResetCode.objects.create(usuario=usuario, codigo=codigo, expiracion=expiracion)
            # Enviar correo
            send_mail(
                'Código de recuperación de contraseña',
                f'Tu código de recuperación es: {codigo}\n\nEste código es válido por 10 minutos.',
                settings.DEFAULT_FROM_EMAIL,
                [usuario.email],
                fail_silently=False,
            )
            request.session['reset_user_id'] = usuario.id
            messages.success(request, 'Te hemos enviado un código de recuperación a tu correo.')
            return redirect('recuperar_password_codigo')
    else:
        form = PasswordResetEmailForm()
    return render(request, 'registration/otp_password_reset_email.html', {'form': form})

# Vista 2: Validar código

def recuperar_password_codigo(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('recuperar_password_email')
    usuario = get_object_or_404(Usuario, id=user_id)
    if request.method == 'POST':
        form = PasswordResetCodeForm(request.POST)
        if form.is_valid():
            codigo = form.cleaned_data['codigo']
            try:
                reset_code = PasswordResetCode.objects.get(usuario=usuario, codigo=codigo, usado=False)
            except PasswordResetCode.DoesNotExist:
                messages.error(request, 'El código es incorrecto o ya fue usado.')
                return render(request, 'registration/otp_password_reset_code.html', {'form': form})
            if not reset_code.es_valido():
                messages.error(request, 'El código ha expirado. Solicita uno nuevo.')
                return redirect('recuperar_password_email')
            request.session['reset_code_id'] = reset_code.id
            return redirect('recuperar_password_nueva')
    else:
        form = PasswordResetCodeForm()
    return render(request, 'registration/otp_password_reset_code.html', {'form': form})

# Vista 3: Nueva contraseña

def recuperar_password_nueva(request):
    code_id = request.session.get('reset_code_id')
    if not code_id:
        return redirect('recuperar_password_email')
    reset_code = get_object_or_404(PasswordResetCode, id=code_id, usado=False)
    usuario = reset_code.usuario
    if request.method == 'POST':
        form = PasswordResetNewPasswordForm(request.POST)
        if form.is_valid():
            nueva = form.cleaned_data['nueva_contraseña']
            usuario.set_password(nueva)
            usuario.save()
            reset_code.usado = True
            reset_code.save()
            login(request, usuario)
            messages.success(request, '¡Contraseña cambiada exitosamente! Ya has iniciado sesión.')
            return redirect('inicio')
    else:
        form = PasswordResetNewPasswordForm()
    return render(request, 'registration/otp_password_reset_new.html', {'form': form})
