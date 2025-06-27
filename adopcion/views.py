from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Mascota, SolicitudAdopcion, Donacion, Favorito, Usuario, PasswordResetCode, HistorialMascota, CitaPreAdopcion, CategoriaDonacion, Notificacion, SeguimientoMascota
from .forms import SolicitudAdopcionForm, CustomUserCreationForm, UserUpdateForm, DonacionForm, MascotaAdminForm, ReporteMensualForm, PasswordResetEmailForm, PasswordResetCodeForm, PasswordResetNewPasswordForm, BusquedaDonantesForm, CategoriaDonacionForm, SeguimientoMascotaForm, MascotaFormMejorado, BusquedaMascotasForm, RegistroUsuarioForm, DonacionFormMejorado, BusquedaDonacionesForm
from .decorators import admin_email_required
from django.db.models import Sum, Count, Q, Avg
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
from django.urls import reverse
from django.contrib.auth.forms import AuthenticationForm

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
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Crear notificación de bienvenida
            crear_notificaciones_registro(user)
            # Enviar correo de bienvenida
            enviar_correo_bienvenida(user)
            messages.success(request, '¡Registro exitoso! Te hemos enviado un correo de bienvenida.')
            return redirect('login')
    else:
        form = RegistroUsuarioForm()
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
    try:
        mascota = Mascota.objects.get(id=mascota_id, estado_adopcion='disponible')
    except Mascota.DoesNotExist:
        messages.error(request, 'La mascota no está disponible para adopción o no existe.')
        return redirect('lista_mascotas')
    
    # Verificar si ya tiene una solicitud pendiente para esta mascota
    if SolicitudAdopcion.objects.filter(usuario=request.user, mascota=mascota, estado_solicitud='pendiente').exists():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'mensaje': f'Ya tienes una solicitud pendiente para {mascota.nombre}.'
            })
        messages.warning(request, f'Ya tienes una solicitud pendiente para {mascota.nombre}.')
        return redirect('mascota_detalle', mascota_id=mascota.id)
    
    if request.method == 'POST':
        form = SolicitudAdopcionForm(request.POST)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.usuario = request.user
            solicitud.mascota = mascota
            solicitud.save()
            mascota.estado_adopcion = 'en_proceso'
            mascota.save()
            # Notificación al usuario y admin
            crear_notificaciones_solicitud(solicitud, 'creada')
            crear_notificaciones_mascota(mascota, 'estado_cambiado')

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

            # Verificar si es una petición AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'mensaje': f'¡Tu solicitud para adoptar a {mascota.nombre} ha sido enviada con éxito! Nos pondremos en contacto contigo pronto.',
                    'redirect': reverse('perfil')
                })

            messages.success(request, f'¡Tu solicitud para adoptar a {mascota.nombre} ha sido enviada con éxito! Nos pondremos en contacto contigo pronto.')
            return redirect('perfil')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'mensaje': 'Por favor corrige los errores en el formulario.',
                    'errors': form.errors
                })
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

@admin_email_required
def admin_dashboard(request):
    # Estadísticas generales
    total_mascotas = Mascota.objects.count()
    mascotas_disponibles = Mascota.objects.filter(estado_adopcion='disponible').count()
    mascotas_en_proceso = Mascota.objects.filter(estado_adopcion='en_proceso').count()
    mascotas_adoptadas = Mascota.objects.filter(estado_adopcion='adoptado').count()
    mascotas_en_tratamiento = Mascota.objects.filter(estado_adopcion='en_tratamiento').count()
    
    peludos_en_fundacion = Mascota.contar_peludos_en_fundacion()
    peludos_adoptados = Mascota.contar_peludos_adoptados()
    
    solicitudes_pendientes = SolicitudAdopcion.objects.filter(estado_solicitud='pendiente').count()
    solicitudes_aprobadas = SolicitudAdopcion.objects.filter(estado_solicitud='aprobada').count()
    solicitudes_rechazadas = SolicitudAdopcion.objects.filter(estado_solicitud='rechazada').count()
    
    total_usuarios = Usuario.objects.count()
    total_donado = Donacion.objects.filter(tipo_donacion='monetaria').aggregate(total=Sum('monto'))['total'] or 0
    
    mascotas_data = {
        'Disponibles': mascotas_disponibles,
        'En Proceso': mascotas_en_proceso,
        'Adoptadas': mascotas_adoptadas,
        'En Tratamiento': mascotas_en_tratamiento
    }
    solicitudes_data = {
        'Pendientes': solicitudes_pendientes,
        'Aprobadas': solicitudes_aprobadas,
        'Rechazadas': solicitudes_rechazadas
    }
    
    # Obtener instancias de categorías por nombre
    alimentos = CategoriaDonacion.objects.filter(nombre__iexact='alimentos').first()
    medicamentos = CategoriaDonacion.objects.filter(nombre__iexact='medicamentos').first()
    juguetes = CategoriaDonacion.objects.filter(nombre__iexact='juguetes').first()
    
    donaciones_monetarias = Donacion.objects.filter(tipo_donacion='monetaria').count()
    donaciones_alimentos = Donacion.objects.filter(tipo_donacion='insumos', categoria_insumo=alimentos).count() if alimentos else 0
    donaciones_medicamentos = Donacion.objects.filter(tipo_donacion='insumos', categoria_insumo=medicamentos).count() if medicamentos else 0
    donaciones_juguetes = Donacion.objects.filter(tipo_donacion='insumos', categoria_insumo=juguetes).count() if juguetes else 0
    donaciones_otros = Donacion.objects.filter(tipo_donacion='insumos').exclude(
        categoria_insumo__in=[c for c in [alimentos, medicamentos, juguetes] if c]
    ).count()
    
    donaciones_data = {
        'Monetarias': donaciones_monetarias,
        'Alimentos': donaciones_alimentos,
        'Medicamentos': donaciones_medicamentos,
        'Juguetes': donaciones_juguetes,
        'Otros': donaciones_otros
    }
    
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

@admin_email_required
def lista_solicitudes(request):
    solicitudes = SolicitudAdopcion.objects.select_related('usuario', 'mascota').order_by('-fecha_solicitud')
    context = {
        'solicitudes': solicitudes
    }
    return render(request, 'adopcion/lista_solicitudes.html', context)

@admin_email_required
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

@admin_email_required
def actualizar_estado_solicitud(request, solicitud_id, nuevo_estado):
    solicitud = get_object_or_404(SolicitudAdopcion, id=solicitud_id)
    estado_anterior = solicitud.estado_solicitud
    solicitud.estado_solicitud = nuevo_estado
    solicitud.save()
    
    # Crear notificaciones según el nuevo estado
    if nuevo_estado == 'aprobada':
        crear_notificaciones_solicitud(solicitud, 'aprobada')
    elif nuevo_estado == 'rechazada':
        crear_notificaciones_solicitud(solicitud, 'rechazada')
    elif nuevo_estado == 'completada':
        crear_notificaciones_solicitud(solicitud, 'completada')
        # Cambiar estado de la mascota a adoptado
        solicitud.mascota.estado_adopcion = 'adoptado'
        solicitud.mascota.save()
        crear_notificaciones_mascota(solicitud.mascota, 'estado_cambiado')
    
    # Enviar correo de notificación
    try:
        enviar_correo_estado_solicitud(solicitud)
    except Exception as e:
        print(f"Error enviando email: {e}")
    
    messages.success(request, f'Estado de la solicitud actualizado a: {solicitud.get_estado_solicitud_display()}')
    return redirect('detalle_solicitud', solicitud_id=solicitud_id)

@admin_email_required
def pagina_reportes(request):
    """Muestra la página con los enlaces para generar los diferentes reportes PDF."""
    form = ReporteMensualForm()
    return render(request, 'adopcion/reportes.html', {'form': form})

@admin_email_required
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

@admin_email_required
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
        form = DonacionForm(request.POST, request.FILES, user=request.user if request.user.is_authenticated else None)
        if form.is_valid():
            donacion = form.save(commit=False)
            if request.user.is_authenticated:
                donacion.usuario = request.user
            donacion.save()
            
            # Crear notificaciones automáticas
            crear_notificaciones_donacion(donacion)
            
            # Enviar correo de agradecimiento
            enviar_correo_donacion(donacion)
            
            # Verificar si es una petición AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'mensaje': '¡Muchas gracias! Tu donación ha sido registrada. Hemos enviado un comprobante a tu correo.',
                    'redirect': reverse('inicio')
                })
            
            messages.success(request, '¡Muchas gracias! Tu donación ha sido registrada. Hemos enviado un comprobante a tu correo.')
            return redirect('inicio')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'mensaje': 'Por favor corrige los errores en el formulario.',
                    'errors': form.errors
                })
    else:
        form = DonacionForm(user=request.user if request.user.is_authenticated else None)

    return render(request, 'adopcion/donacion_form_mejorado.html', {'form': form})

# Vistas para el sistema de favoritos
@login_required
@require_POST
def agregar_favorito(request, mascota_id):
    mascota = get_object_or_404(Mascota, id=mascota_id)
    favorito, created = Favorito.objects.get_or_create(
        usuario=request.user,
        mascota=mascota
    )
    return JsonResponse({
        'success': True,
        'is_favorite': True,
        'message': f'{mascota.nombre} añadido a tus favoritos.' if created else f'{mascota.nombre} ya estaba en tus favoritos.'
    })

@login_required
@require_POST
def quitar_favorito(request, mascota_id):
    mascota = get_object_or_404(Mascota, id=mascota_id)
    try:
        favorito = Favorito.objects.get(usuario=request.user, mascota=mascota)
        favorito.delete()
        return JsonResponse({'success': True, 'is_favorite': False, 'message': f'{mascota.nombre} ha sido removido de tus favoritos.'})
    except Favorito.DoesNotExist:
        return JsonResponse({'success': False, 'is_favorite': False, 'message': 'Favorito no encontrado.'})

@login_required
def mis_favoritos(request):
    """Vista para mostrar las mascotas favoritas del usuario"""
    mascotas = Mascota.objects.filter(seguidores__usuario=request.user).order_by('-fecha_ingreso')
    tipo = request.GET.get('tipo', '')
    edad = request.GET.get('edad', '')
    if tipo:
        mascotas = mascotas.filter(tipo=tipo)
    if edad:
        if edad == '2-12':
            mascotas = mascotas.filter(edad_aproximada_meses__gte=2, edad_aproximada_meses__lte=12)
        elif edad == '13-24':
            mascotas = mascotas.filter(edad_aproximada_meses__gte=13, edad_aproximada_meses__lte=24)
        elif edad == '25-48':
            mascotas = mascotas.filter(edad_aproximada_meses__gte=25, edad_aproximada_meses__lte=48)
        elif edad == '49+':
            mascotas = mascotas.filter(edad_aproximada_meses__gte=49)
    filtros_activos = {'tipo': tipo, 'edad': edad}
    return render(request, 'adopcion/mis_favoritos.html', {'mascotas': mascotas, 'filtros_activos': filtros_activos})

@admin_email_required
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

@admin_email_required
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

@admin_email_required
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

@admin_email_required
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

@admin_email_required
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

@admin_email_required
def editar_mascota(request, mascota_id):
    mascota = get_object_or_404(Mascota, id=mascota_id)
    if request.method == 'POST':
        form = MascotaAdminForm(request.POST, request.FILES, instance=mascota)
        if form.is_valid():
            estado_anterior = mascota.estado_adopcion
            mascota = form.save()
            nuevo_estado = mascota.estado_adopcion
            if estado_anterior != nuevo_estado:
                HistorialMascota.objects.create(
                    mascota=mascota,
                    estado_anterior=estado_anterior,
                    estado_nuevo=nuevo_estado,
                    usuario=request.user
                )
            messages.success(request, f'Los datos de {mascota.nombre} han sido actualizados.')
            return redirect('admin_dashboard')
    else:
        form = MascotaAdminForm(instance=mascota)
    return render(request, 'adopcion/agregar_mascota.html', {
        'form': form,
        'titulo': f'Editar a {mascota.nombre}'
    })

def lista_mascotas(request):
    """Vista para listar todas las mascotas disponibles con filtros"""
    mascotas_list = Mascota.objects.filter(estado_adopcion='disponible').order_by('-fecha_ingreso')
    
    # Filtros
    tipo_filter = request.GET.get('tipo', '')
    edad_min_filter = request.GET.get('edad_min', '')
    edad_max_filter = request.GET.get('edad_max', '')
    sexo_filter = request.GET.get('sexo', '')
    tamaño_filter = request.GET.get('tamaño', '')
    q_filter = request.GET.get('q', '')
    
    # Aplicar filtros
    if tipo_filter:
        mascotas_list = mascotas_list.filter(tipo=tipo_filter)
    if edad_min_filter:
        mascotas_list = mascotas_list.filter(edad_aproximada_meses__gte=edad_min_filter)
    if edad_max_filter:
        mascotas_list = mascotas_list.filter(edad_aproximada_meses__lte=edad_max_filter)
    if sexo_filter:
        mascotas_list = mascotas_list.filter(sexo=sexo_filter)
    if tamaño_filter:
        mascotas_list = mascotas_list.filter(tamaño=tamaño_filter)
    if q_filter:
        mascotas_list = mascotas_list.filter(
            Q(nombre__icontains=q_filter) |
            Q(raza__icontains=q_filter) |
            Q(descripcion__icontains=q_filter) |
            Q(personalidad__icontains=q_filter) |
            Q(color__icontains=q_filter)
        )
    # Carrusel: hasta 6 mascotas reales, disponibles y con imagen principal válida
    mascotas_carousel = Mascota.objects.filter(estado_adopcion='disponible').exclude(imagen_principal='').exclude(imagen_principal__isnull=True).order_by('-fecha_ingreso')[:6]
    # Estadísticas
    total_mascotas = mascotas_list.count()
    perros = mascotas_list.filter(tipo='perro').count()
    gatos = mascotas_list.filter(tipo='gato').count()
    disponibles = mascotas_list.filter(estado_adopcion='disponible').count()
    # Paginación
    paginator = Paginator(mascotas_list, 12)
    page = request.GET.get('page')
    try:
        mascotas = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        mascotas = paginator.page(1)
    # Choices para los filtros
    tipos = Mascota.TIPO_CHOICES
    sexos = Mascota.SEXO_CHOICES
    tamaños = Mascota.TAMAÑO_CHOICES
    context = {
        'mascotas': mascotas,
        'mascotas_carousel': mascotas_carousel,
        'total_mascotas': total_mascotas,
        'perros': perros,
        'gatos': gatos,
        'disponibles': disponibles,
        'tipos': tipos,
        'sexos': sexos,
        'tamaños': tamaños,
        'filtros_actuales': {
            'tipo': tipo_filter,
            'edad_min': edad_min_filter,
            'edad_max': edad_max_filter,
            'sexo': sexo_filter,
            'tamaño': tamaño_filter,
            'q': q_filter,
        },
        'filtros_aplicados': any([
            tipo_filter, edad_min_filter, edad_max_filter, sexo_filter, tamaño_filter, q_filter
        ]),
        'total_results': total_mascotas,
        'total_original': Mascota.objects.count(),
    }
    return render(request, 'adopcion/lista_mascotas.html', context)

@admin_email_required
@require_http_methods(["GET", "POST"])
def admin_editar_mascotas(request):
    """Vista para que el administrador edite múltiples mascotas a la vez"""
    if request.method == 'POST':
        mascotas = Mascota.objects.all()
        for mascota in mascotas:
            # Obtener los datos del formulario para cada mascota
            nombre = request.POST.get(f'nombre_{mascota.id}')
            tipo = request.POST.get(f'tipo_{mascota.id}')
            raza = request.POST.get(f'raza_{mascota.id}')
            edad = request.POST.get(f'edad_{mascota.id}')
            sexo = request.POST.get(f'sexo_{mascota.id}')
            tamaño = request.POST.get(f'tamaño_{mascota.id}')
            estado = request.POST.get(f'estado_{mascota.id}')
            
            # Actualizar solo si hay cambios
            if nombre and nombre != mascota.nombre:
                mascota.nombre = nombre
            if tipo and tipo != mascota.tipo:
                mascota.tipo = tipo
            if raza and raza != mascota.raza:
                mascota.raza = raza
            if edad and int(edad) != mascota.edad_aproximada_meses:
                mascota.edad_aproximada_meses = int(edad)
            if sexo and sexo != mascota.sexo:
                mascota.sexo = sexo
            if tamaño and tamaño != mascota.tamaño:
                mascota.tamaño = tamaño
            if estado and estado != mascota.estado_adopcion:
                mascota.estado_adopcion = estado
            
            mascota.save()
        
        messages.success(request, 'Mascotas actualizadas exitosamente.')
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

@admin_email_required
def busqueda_donantes(request):
    """Vista para búsqueda múltiple de donantes con estadísticas mejoradas"""
    form = BusquedaDonantesForm(request.GET or None)
    donaciones = Donacion.objects.all()
    
    # Variables para estadísticas
    total_original = donaciones.count()
    filtros_aplicados = False
    
    if form.is_valid():
        # Aplicar filtros
        if form.cleaned_data.get('nombre'):
            donaciones = donaciones.filter(
                Q(nombre_donante__icontains=form.cleaned_data['nombre']) |
                Q(apellido_donante__icontains=form.cleaned_data['nombre'])
            )
            filtros_aplicados = True
        if form.cleaned_data.get('apellido'):
            donaciones = donaciones.filter(apellido_donante__icontains=form.cleaned_data['apellido'])
            filtros_aplicados = True
        if form.cleaned_data.get('email'):
            donaciones = donaciones.filter(email_donante__icontains=form.cleaned_data['email'])
            filtros_aplicados = True
        if form.cleaned_data.get('tipo_donacion'):
            donaciones = donaciones.filter(tipo_donacion=form.cleaned_data['tipo_donacion'])
            filtros_aplicados = True
        if form.cleaned_data.get('categoria'):
            donaciones = donaciones.filter(categoria_insumo=form.cleaned_data['categoria'])
            filtros_aplicados = True
        if form.cleaned_data.get('fecha_desde'):
            donaciones = donaciones.filter(fecha_donacion__date__gte=form.cleaned_data['fecha_desde'])
            filtros_aplicados = True
        if form.cleaned_data.get('fecha_hasta'):
            donaciones = donaciones.filter(fecha_donacion__date__lte=form.cleaned_data['fecha_hasta'])
            filtros_aplicados = True
    
    # Estadísticas mejoradas
    total_donaciones = donaciones.count()
    total_monetario = donaciones.filter(tipo_donacion='monetaria').aggregate(total=Sum('monto'))['total'] or 0
    total_insumos = donaciones.filter(tipo_donacion='insumos').count()
    total_servicios = donaciones.filter(tipo_donacion='servicios').count()
    total_especie = donaciones.filter(tipo_donacion='especie').count()
    
    # Contar donantes únicos
    donantes_unicos = donaciones.values('email_donante').distinct().count()
    
    # Estadísticas por tipo de donación
    estadisticas_por_tipo = {}
    for tipo_choice in Donacion.TIPO_DONACION_CHOICES:
        count = donaciones.filter(tipo_donacion=tipo_choice[0]).count()
        if count > 0:
            estadisticas_por_tipo[tipo_choice[1]] = count
    
    # Estadísticas por estado de donación
    estadisticas_por_estado = {}
    for estado_choice in Donacion.objects.values_list('estado_donacion', flat=True).distinct():
        count = donaciones.filter(estado_donacion=estado_choice).count()
        if count > 0:
            estadisticas_por_estado[estado_choice] = count
    
    # Estadísticas por frecuencia
    estadisticas_por_frecuencia = {}
    for frecuencia_choice in Donacion.FRECUENCIA_CHOICES:
        count = donaciones.filter(frecuencia=frecuencia_choice[0]).count()
        if count > 0:
            estadisticas_por_frecuencia[frecuencia_choice[1]] = count
    
    # Estadísticas por categoría (solo para insumos)
    estadisticas_categoria = {}
    if form.is_valid() and form.cleaned_data.get('tipo_donacion') == 'insumos':
        categorias = CategoriaDonacion.objects.filter(activa=True)
        for categoria in categorias:
            count = donaciones.filter(categoria_insumo=categoria).count()
            if count > 0:
                estadisticas_categoria[categoria.nombre] = count
    
    # Top 5 donantes más generosos (por monto total)
    top_donantes = donaciones.filter(tipo_donacion='monetaria').values(
        'nombre_donante', 'apellido_donante', 'email_donante'
    ).annotate(
        total_donado=Sum('monto'),
        num_donaciones=Count('id')
    ).order_by('-total_donado')[:5]
    
    # Paginación
    paginator = Paginator(donaciones.order_by('-fecha_donacion'), 20)
    page = request.GET.get('page')
    try:
        donaciones_paginadas = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        donaciones_paginadas = paginator.page(1)
    
    context = {
        'form': form,
        'donaciones': donaciones_paginadas,
        'total_donaciones': total_donaciones,
        'total_original': total_original,
        'total_monetario': total_monetario,
        'total_insumos': total_insumos,
        'total_servicios': total_servicios,
        'total_especie': total_especie,
        'donantes_unicos': donantes_unicos,
        'filtros_aplicados': filtros_aplicados,
        'estadisticas_por_tipo': estadisticas_por_tipo,
        'estadisticas_por_estado': estadisticas_por_estado,
        'estadisticas_por_frecuencia': estadisticas_por_frecuencia,
        'estadisticas_categoria': estadisticas_categoria,
        'top_donantes': top_donantes,
    }
    return render(request, 'adopcion/busqueda_donantes.html', context)

@admin_email_required
def gestionar_categorias(request):
    """Vista para gestionar categorías de donaciones"""
    if request.method == 'POST':
        form = CategoriaDonacionForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f'Categoría "{categoria.nombre}" creada exitosamente.')
            return redirect('gestionar_categorias')
    else:
        form = CategoriaDonacionForm()
    
    categorias = CategoriaDonacion.objects.all().order_by('nombre')
    
    context = {
        'form': form,
        'categorias': categorias,
    }
    return render(request, 'adopcion/gestionar_categorias.html', context)

@admin_email_required
def editar_categoria(request, categoria_id):
    """Vista para editar una categoría"""
    categoria = get_object_or_404(CategoriaDonacion, id=categoria_id)
    
    if request.method == 'POST':
        form = CategoriaDonacionForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada exitosamente.')
            return redirect('gestionar_categorias')
    else:
        form = CategoriaDonacionForm(instance=categoria)
    
    context = {
        'form': form,
        'categoria': categoria,
    }
    return render(request, 'adopcion/editar_categoria.html', context)

@admin_email_required
def eliminar_categoria(request, categoria_id):
    """Vista para eliminar una categoría"""
    categoria = get_object_or_404(CategoriaDonacion, id=categoria_id)
    
    if request.method == 'POST':
        # Verificar si hay donaciones usando esta categoría
        donaciones_count = Donacion.objects.filter(categoria_insumo=categoria).count()
        if donaciones_count > 0:
            messages.error(request, f'No se puede eliminar la categoría porque hay {donaciones_count} donaciones asociadas.')
        else:
            categoria.delete()
            messages.success(request, 'Categoría eliminada exitosamente.')
        return redirect('gestionar_categorias')
    
    context = {
        'categoria': categoria,
        'donaciones_count': Donacion.objects.filter(categoria_insumo=categoria).count(),
    }
    return render(request, 'adopcion/eliminar_categoria.html', context)

@login_required
def notificaciones(request):
    """Vista para mostrar notificaciones del usuario con filtros"""
    notificaciones_list = Notificacion.objects.filter(usuario=request.user)
    
    # Filtros
    tipo_filter = request.GET.get('tipo', '')
    estado_filter = request.GET.get('estado', '')
    
    if tipo_filter:
        notificaciones_list = notificaciones_list.filter(tipo=tipo_filter)
    
    if estado_filter == 'no_leidas':
        notificaciones_list = notificaciones_list.filter(leida=False)
    elif estado_filter == 'leidas':
        notificaciones_list = notificaciones_list.filter(leida=True)
    
    # Ordenar por fecha de creación (más recientes primero)
    notificaciones_list = notificaciones_list.order_by('-fecha_creacion')
    
    # Marcar como leídas las notificaciones no leídas si no hay filtros específicos
    if not tipo_filter and not estado_filter:
        notificaciones_no_leidas = notificaciones_list.filter(leida=False)
        if notificaciones_no_leidas.exists():
            notificaciones_no_leidas.update(leida=True, fecha_lectura=timezone.now())
    
    # Estadísticas
    total_notificaciones = Notificacion.objects.filter(usuario=request.user).count()
    notificaciones_no_leidas_count = Notificacion.objects.filter(usuario=request.user, leida=False).count()
    
    # Tipos de notificaciones disponibles para el filtro (sin duplicados)
    tipos_disponibles = list(set(Notificacion.objects.filter(usuario=request.user).values_list('tipo', flat=True)))
    
    # Paginación
    paginator = Paginator(notificaciones_list, 15)
    page = request.GET.get('page')
    try:
        notificaciones_paginadas = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        notificaciones_paginadas = paginator.page(1)
    
    context = {
        'notificaciones': notificaciones_paginadas,
        'total_notificaciones': total_notificaciones,
        'notificaciones_no_leidas_count': notificaciones_no_leidas_count,
        'tipos_disponibles': tipos_disponibles,
        'filtros_activos': {
            'tipo': tipo_filter,
            'estado': estado_filter,
        },
        'es_admin': request.user.rol == 'administrador',
    }
    return render(request, 'adopcion/notificaciones.html', context)

@login_required
def marcar_notificacion_leida(request, notificacion_id):
    """Vista para marcar una notificación como leída"""
    notificacion = get_object_or_404(Notificacion, id=notificacion_id, usuario=request.user)
    notificacion.leida = True
    notificacion.fecha_lectura = timezone.now()
    notificacion.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notificaciones')

def crear_notificacion(usuario, tipo, titulo, mensaje, solicitud=None, mascota=None, donacion=None):
    """Función base para crear notificaciones"""
    try:
        notificacion = Notificacion.objects.create(
            usuario=usuario,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            solicitud=solicitud,
            mascota=mascota,
            donacion=donacion,
            fecha_creacion=timezone.now()
        )
        return notificacion
    except Exception as e:
        print(f"Error creando notificación: {e}")
        return None

def crear_notificaciones_registro(usuario):
    """Crear notificación de bienvenida al registrarse"""
    crear_notificacion(
        usuario=usuario,
        tipo='bienvenida',
        titulo='¡Bienvenido a Luna & Lía! 🐾',
        mensaje=f'Hola {usuario.nombre}, ¡gracias por unirte a nuestra comunidad! Ahora puedes explorar nuestras mascotas disponibles para adopción, hacer donaciones y ser parte de nuestra misión de rescatar huellas. ¡Bienvenido!'
    )

def crear_notificaciones_inicio_sesion(usuario):
    """Crear notificación de inicio de sesión exitoso para usuario y administradores"""
    # Notificación para el usuario
    crear_notificacion(
        usuario=usuario,
        tipo='sesion',
        titulo='Inicio de sesión exitoso ✅',
        mensaje=f'¡Hola {usuario.nombre}! Has iniciado sesión correctamente. ¡Disfruta explorando nuestras mascotas!'
    )
    # Notificación para todos los administradores
    administradores = Usuario.objects.filter(rol='administrador')
    for admin in administradores:
        crear_notificacion(
            usuario=admin,
            tipo='sesion_admin',
            titulo='Nuevo inicio de sesión',
            mensaje=f'El usuario {usuario.nombre} ({usuario.email}) ha iniciado sesión en el sistema.'
        )

def crear_notificaciones_solicitud(solicitud, accion):
    """Crear notificaciones relacionadas con solicitudes de adopción"""
    usuario = solicitud.usuario
    mascota = solicitud.mascota
    
    if accion == 'creada':
        # Notificación para el usuario que hizo la solicitud
        crear_notificacion(
            usuario=usuario,
            tipo='solicitud',
            titulo=f'Solicitud enviada para {mascota.nombre} 📋',
            mensaje=f'Tu solicitud para adoptar a {mascota.nombre} ha sido enviada exitosamente. Nos pondremos en contacto contigo pronto para coordinar los siguientes pasos.'
        )
        
        # Notificaciones para todos los administradores
        administradores = Usuario.objects.filter(rol='administrador')
        for admin in administradores:
            crear_notificacion(
                usuario=admin,
                tipo='nueva_solicitud_admin',
                titulo=f'Nueva solicitud de adopción - {mascota.nombre}',
                mensaje=f'El usuario {usuario.get_full_name()} ha solicitado adoptar a {mascota.nombre}. Revisa los detalles en el panel de administración.',
                solicitud=solicitud,
                mascota=mascota
            )
    
    elif accion == 'aprobada':
        crear_notificacion(
            usuario=usuario,
            tipo='solicitud_aprobada',
            titulo=f'¡Solicitud aprobada! 🎉',
            mensaje=f'¡Excelentes noticias! Tu solicitud para adoptar a {mascota.nombre} ha sido aprobada. Te contactaremos para coordinar la adopción.'
        )
        
        # Notificar a administradores sobre la aprobación
        administradores = Usuario.objects.filter(rol='administrador')
        for admin in administradores:
            crear_notificacion(
                usuario=admin,
                tipo='solicitud_aprobada_admin',
                titulo=f'Solicitud aprobada - {mascota.nombre}',
                mensaje=f'La solicitud de {usuario.get_full_name()} para adoptar a {mascota.nombre} ha sido aprobada.',
                solicitud=solicitud,
                mascota=mascota
            )
    
    elif accion == 'rechazada':
        crear_notificacion(
            usuario=usuario,
            tipo='solicitud_rechazada',
            titulo=f'Solicitud de adopción - {mascota.nombre}',
            mensaje=f'Lamentamos informarte que tu solicitud para adoptar a {mascota.nombre} no pudo ser aprobada en esta ocasión. Te invitamos a revisar otras mascotas disponibles.'
        )
    
    elif accion == 'completada':
        crear_notificacion(
            usuario=usuario,
            tipo='adopcion_completada',
            titulo=f'¡Adopción completada! 🏠',
            mensaje=f'¡Felicidades! La adopción de {mascota.nombre} se ha completado exitosamente. ¡Que disfruten su nueva vida juntos!'
        )

def crear_notificaciones_donacion(donacion):
    """Crear notificaciones relacionadas con donaciones"""
    # Notificación para el donante
    crear_notificacion(
        usuario=donacion.usuario if donacion.usuario else None,
        tipo='donacion',
        titulo='¡Gracias por tu donación! 💝',
        mensaje=f'¡Muchas gracias por tu donación de {donacion.get_tipo_donacion_display().lower()}! Tu generosidad nos ayuda a seguir rescatando y cuidando mascotas. Te hemos enviado un comprobante por correo.'
    )
    
    # Notificaciones para administradores sobre nueva donación
    administradores = Usuario.objects.filter(rol='administrador')
    for admin in administradores:
        crear_notificacion(
            usuario=admin,
            tipo='nueva_donacion_admin',
            titulo=f'Nueva donación recibida - {donacion.get_tipo_donacion_display()}',
            mensaje=f'Se ha recibido una nueva donación de {donacion.nombre_donante} {donacion.apellido_donante} por {donacion.get_tipo_donacion_display().lower()}.',
            donacion=donacion
        )

def crear_notificaciones_mascota(mascota, accion):
    """Crear notificaciones relacionadas con mascotas"""
    if accion == 'nueva':
        # Notificar a administradores sobre nueva mascota
        administradores = Usuario.objects.filter(rol='administrador')
        for admin in administradores:
            crear_notificacion(
                usuario=admin,
                tipo='nueva_mascota_admin',
                titulo=f'Nueva mascota agregada - {mascota.nombre}',
                mensaje=f'Se ha agregado una nueva mascota: {mascota.nombre} ({mascota.get_tipo_display()}, {mascota.get_sexo_display()}).',
                mascota=mascota
            )
        
        # Notificar a usuarios que tienen favoritos similares
        usuarios_interesados = Usuario.objects.filter(
            favoritos__mascota__tipo=mascota.tipo
        ).distinct()
        
        for usuario in usuarios_interesados:
            crear_notificacion(
                usuario=usuario,
                tipo='nueva_mascota_similar',
                titulo=f'Nueva mascota disponible - {mascota.nombre}',
                mensaje=f'¡Hola {usuario.nombre}! Tenemos una nueva mascota {mascota.get_tipo_display()} que podría interesarte: {mascota.nombre}. ¡Ven a conocerla!',
                mascota=mascota
            )
    
    elif accion == 'actualizada':
        # Notificar a administradores sobre actualización
        administradores = Usuario.objects.filter(rol='administrador')
        for admin in administradores:
            crear_notificacion(
                usuario=admin,
                tipo='mascota_actualizada_admin',
                titulo=f'Mascota actualizada - {mascota.nombre}',
                mensaje=f'La información de {mascota.nombre} ha sido actualizada.',
                mascota=mascota
            )
    
    elif accion == 'estado_cambiado':
        # Notificar cambio de estado
        administradores = Usuario.objects.filter(rol='administrador')
        for admin in administradores:
            crear_notificacion(
                usuario=admin,
                tipo='estado_mascota_admin',
                titulo=f'Estado cambiado - {mascota.nombre}',
                mensaje=f'El estado de {mascota.nombre} ha cambiado a: {mascota.get_estado_adopcion_display()}.',
                mascota=mascota
            )

def crear_notificaciones_cita(cita, accion):
    """Crear notificaciones relacionadas con citas de pre-adopción"""
    if accion == 'creada':
        # Notificar al usuario sobre la cita
        crear_notificacion(
            usuario=cita.solicitud.usuario,
            tipo='cita_creada',
            titulo=f'Cita programada - {cita.solicitud.mascota.nombre} 📅',
            mensaje=f'Se ha programado una cita para conocer a {cita.solicitud.mascota.nombre} el {cita.fecha_cita.strftime("%d/%m/%Y")} a las {cita.hora_cita.strftime("%H:%M")}.'
        )
        
        # Notificar a administradores
        administradores = Usuario.objects.filter(rol='administrador')
        for admin in administradores:
            crear_notificacion(
                usuario=admin,
                tipo='cita_creada_admin',
                titulo=f'Nueva cita programada - {cita.solicitud.mascota.nombre}',
                mensaje=f'Se ha programado una cita con {cita.solicitud.usuario.get_full_name()} para {cita.solicitud.mascota.nombre}.',
                mascota=cita.solicitud.mascota
            )

def crear_notificaciones_seguimiento(seguimiento):
    """Crear notificaciones relacionadas con seguimientos"""
    mascota = seguimiento.mascota
    
    # Notificar a administradores sobre nuevo seguimiento
    administradores = Usuario.objects.filter(rol='administrador')
    for admin in administradores:
        crear_notificacion(
            usuario=admin,
            tipo='nuevo_seguimiento_admin',
            titulo=f'Nuevo seguimiento - {mascota.nombre}',
            mensaje=f'Se ha registrado un nuevo seguimiento para {mascota.nombre} con peso: {seguimiento.peso}kg.',
            mascota=mascota
        )

def crear_notificaciones_solicitudes_pendientes():
    """Crear notificaciones diarias sobre solicitudes pendientes para administradores"""
    solicitudes_pendientes = SolicitudAdopcion.objects.filter(estado_solicitud='pendiente').count()
    
    if solicitudes_pendientes > 0:
        administradores = Usuario.objects.filter(rol='administrador')
        for admin in administradores:
            crear_notificacion(
                usuario=admin,
                tipo='recordatorio_admin',
                titulo=f'Recordatorio: {solicitudes_pendientes} solicitudes pendientes',
                mensaje=f'Hay {solicitudes_pendientes} solicitudes de adopción pendientes de revisión. Por favor, revisa el panel de administración.'
            )

def crear_notificaciones_donaciones_recientes():
    """Crear notificaciones sobre donaciones recientes para administradores"""
    from datetime import timedelta
    
    # Donaciones de las últimas 24 horas
    donaciones_recientes = Donacion.objects.filter(
        fecha_donacion__gte=timezone.now() - timedelta(days=1)
    ).count()
    
    if donaciones_recientes > 0:
        administradores = Usuario.objects.filter(rol='administrador')
        for admin in administradores:
            crear_notificacion(
                usuario=admin,
                tipo='resumen_donaciones_admin',
                titulo=f'Resumen: {donaciones_recientes} donaciones en las últimas 24h',
                mensaje=f'Se han recibido {donaciones_recientes} donaciones en las últimas 24 horas. Revisa el panel de administración para más detalles.'
            )

@admin_email_required
def seguimiento_mascota(request, mascota_id):
    """Vista para registrar seguimientos de mascotas"""
    mascota = get_object_or_404(Mascota, id=mascota_id)
    
    if request.method == 'POST':
        form = SeguimientoMascotaForm(request.POST)
        if form.is_valid():
            seguimiento = form.save(commit=False)
            seguimiento.mascota = mascota
            seguimiento.id_admin_seguimiento = request.user
            seguimiento.save()
            
            # Crear notificación automática
            crear_notificaciones_seguimiento(seguimiento)
            
            messages.success(request, f'Seguimiento registrado exitosamente para {mascota.nombre}.')
            return redirect('admin_editar_mascotas')
    else:
        form = SeguimientoMascotaForm()
    
    # Obtener historial de seguimientos
    seguimientos = SeguimientoMascota.objects.filter(mascota=mascota).order_by('-fecha_seguimiento')
    
    context = {
        'mascota': mascota,
        'form': form,
        'seguimientos': seguimientos,
    }
    return render(request, 'adopcion/seguimiento_mascota.html', context)

@admin_email_required
def agregar_mascota_mejorado(request):
    """Vista mejorada para agregar mascotas"""
    if request.method == 'POST':
        form = MascotaFormMejorado(request.POST, request.FILES)
        if form.is_valid():
            mascota = form.save(commit=False)
            mascota.id_admin_registro = request.user
            mascota.fecha_ingreso = timezone.now().date()
            mascota.save()
            
            # Crear notificación automática
            crear_notificaciones_mascota(mascota, 'nueva')
            
            # Verificar si es una petición AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'mensaje': f'Mascota {mascota.nombre} agregada exitosamente.',
                    'redirect': reverse('admin_dashboard')
                })
            
            messages.success(request, f'Mascota {mascota.nombre} agregada exitosamente.')
            return redirect('admin_dashboard')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'mensaje': 'Por favor corrige los errores en el formulario.',
                    'errors': form.errors
                })
    else:
        form = MascotaFormMejorado()
    
    context = {
        'form': form,
        'razas_perros': MascotaFormMejorado.RAZAS_PERROS,
        'razas_gatos': MascotaFormMejorado.RAZAS_GATOS,
    }
    return render(request, 'adopcion/agregar_mascota_mejorado.html', context)

@admin_email_required
def editar_mascota_mejorado(request, mascota_id):
    """Vista mejorada para editar mascotas"""
    mascota = get_object_or_404(Mascota, id=mascota_id)
    
    if request.method == 'POST':
        form = MascotaFormMejorado(request.POST, request.FILES, instance=mascota)
        if form.is_valid():
            mascota = form.save()
            
            # Crear notificación automática
            crear_notificaciones_mascota(mascota, 'actualizada')
            
            # Verificar si es una petición AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'mensaje': f'Mascota {mascota.nombre} actualizada exitosamente.',
                    'redirect': reverse('admin_dashboard')
                })
            
            messages.success(request, f'Mascota {mascota.nombre} actualizada exitosamente.')
            return redirect('admin_dashboard')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'mensaje': 'Por favor corrige los errores en el formulario.',
                    'errors': form.errors
                })
    else:
        form = MascotaFormMejorado(instance=mascota)
    
    context = {
        'form': form,
        'mascota': mascota,
        'razas_perros': MascotaFormMejorado.RAZAS_PERROS,
        'razas_gatos': MascotaFormMejorado.RAZAS_GATOS,
    }
    return render(request, 'adopcion/agregar_mascota_mejorado.html', context)

@login_required
def realizar_donacion_mejorado(request):
    """Vista mejorada para realizar donaciones - requiere autenticación"""
    if request.method == 'POST':
        form = DonacionFormMejorado(request.POST, request.FILES, usuario=request.user)
        if form.is_valid():
            donacion = form.save()
            
            # Crear notificación para el usuario
            crear_notificaciones_donacion(donacion)
            
            # Enviar correo de agradecimiento
            try:
                enviar_correo_donacion(donacion)
            except Exception as e:
                print(f"Error enviando email de donación: {e}")
            
            messages.success(request, '¡Gracias por tu donación! Te hemos enviado un correo de confirmación.')
            return redirect('perfil')
    else:
        form = DonacionFormMejorado(usuario=request.user)
    
    # Obtener categorías activas para el formulario
    categorias = CategoriaDonacion.objects.filter(activa=True)
    
    context = {
        'form': form,
        'categorias': categorias,
        'usuario': request.user
    }
    return render(request, 'adopcion/donacion_form_mejorado.html', context)

@login_required
def obtener_notificaciones_ajax(request):
    """Vista AJAX para obtener notificaciones no leídas"""
    notificaciones = Notificacion.objects.filter(
        usuario=request.user, 
        leida=False
    ).order_by('-fecha_creacion')[:5]
    
    data = []
    for notif in notificaciones:
        data.append({
            'id': notif.id,
            'tipo': notif.tipo,
            'titulo': notif.titulo,
            'mensaje': notif.mensaje,
            'fecha': notif.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
        })
    
    return JsonResponse({'notificaciones': data, 'count': len(data)})

@admin_email_required
def busqueda_mascotas_avanzada(request):
    """Vista para búsqueda avanzada de mascotas con filtros múltiples y estadísticas mejoradas"""
    form = BusquedaMascotasForm(request.GET or None)
    mascotas = Mascota.objects.filter(estado_adopcion='disponible').order_by('-fecha_ingreso')
    
    # Variables para estadísticas
    total_original = mascotas.count()
    filtros_aplicados = False
    
    if form.is_valid():
        # Aplicar filtros
        if form.cleaned_data.get('q'):
            query = form.cleaned_data['q']
            mascotas = mascotas.filter(
                Q(nombre__icontains=query) |
                Q(raza__icontains=query) |
                Q(descripcion__icontains=query) |
                Q(personalidad__icontains=query) |
                Q(color__icontains=query)
            )
            filtros_aplicados = True
        
        if form.cleaned_data.get('tipo'):
            mascotas = mascotas.filter(tipo=form.cleaned_data['tipo'])
            filtros_aplicados = True
        
        if form.cleaned_data.get('categoria'):
            mascotas = mascotas.filter(categoria=form.cleaned_data['categoria'])
            filtros_aplicados = True
        
        if form.cleaned_data.get('sexo'):
            mascotas = mascotas.filter(sexo=form.cleaned_data['sexo'])
            filtros_aplicados = True
        
        if form.cleaned_data.get('tamaño'):
            mascotas = mascotas.filter(tamaño=form.cleaned_data['tamaño'])
            filtros_aplicados = True
        
        if form.cleaned_data.get('estado_adopcion'):
            mascotas = mascotas.filter(estado_adopcion=form.cleaned_data['estado_adopcion'])
            filtros_aplicados = True
        
        if form.cleaned_data.get('edad_min'):
            mascotas = mascotas.filter(edad_aproximada_meses__gte=form.cleaned_data['edad_min'])
            filtros_aplicados = True
        
        if form.cleaned_data.get('edad_max'):
            mascotas = mascotas.filter(edad_aproximada_meses__lte=form.cleaned_data['edad_max'])
            filtros_aplicados = True
        
        if form.cleaned_data.get('peso_min'):
            mascotas = mascotas.filter(peso__gte=form.cleaned_data['peso_min'])
            filtros_aplicados = True
        
        if form.cleaned_data.get('peso_max'):
            mascotas = mascotas.filter(peso__lte=form.cleaned_data['peso_max'])
            filtros_aplicados = True
    
    # Estadísticas mejoradas
    total_mascotas = mascotas.count()
    
    # Estadísticas por estado
    estadisticas_por_estado = {}
    for estado_choice in Mascota.ESTADO_ADOPCION_CHOICES:
        count = mascotas.filter(estado_adopcion=estado_choice[0]).count()
        if count > 0:
            estadisticas_por_estado[estado_choice[1]] = count
    
    # Estadísticas por categoría
    estadisticas_por_categoria = {}
    for categoria_choice in Mascota.CATEGORIA_CHOICES:
        count = mascotas.filter(categoria=categoria_choice[0]).count()
        if count > 0:
            estadisticas_por_categoria[categoria_choice[1]] = count
    
    # Estadísticas por tipo
    estadisticas_por_tipo = {}
    for tipo_choice in Mascota.TIPO_CHOICES:
        count = mascotas.filter(tipo=tipo_choice[0]).count()
        if count > 0:
            estadisticas_por_tipo[tipo_choice[1]] = count
    
    # Estadísticas por sexo
    estadisticas_por_sexo = {}
    for sexo_choice in Mascota.SEXO_CHOICES:
        count = mascotas.filter(sexo=sexo_choice[0]).count()
        if count > 0:
            estadisticas_por_sexo[sexo_choice[1]] = count
    
    # Estadísticas por tamaño
    estadisticas_por_tamaño = {}
    for tamaño_choice in Mascota.TAMAÑO_CHOICES:
        count = mascotas.filter(tamaño=tamaño_choice[0]).count()
        if count > 0:
            estadisticas_por_tamaño[tamaño_choice[1]] = count
    
    # Estadísticas adicionales
    mascotas_disponibles = mascotas.filter(estado_adopcion='disponible').count()
    mascotas_en_proceso = mascotas.filter(estado_adopcion='en_proceso').count()
    mascotas_adoptadas = mascotas.filter(estado_adopcion='adoptado').count()
    mascotas_esterilizadas = mascotas.filter(esterilizado=True).count()
    mascotas_vacunadas = mascotas.filter(vacunas_completas=True).count()
    mascotas_con_microchip = mascotas.filter(microchip=True).count()
    
    # Promedio de edad y peso
    promedio_edad = mascotas.aggregate(avg_edad=Avg('edad_aproximada_meses'))['avg_edad'] or 0
    promedio_peso = mascotas.aggregate(avg_peso=Avg('peso'))['avg_peso'] or 0
    
    # Mascotas más populares (por número de favoritos)
    mascotas_populares = mascotas.annotate(
        num_favoritos=Count('seguidores')
    ).order_by('-num_favoritos')[:5]
    
    # Mascotas más antiguas en la fundación
    mascotas_antiguas = mascotas.order_by('fecha_ingreso')[:5]
    
    # Paginación
    paginator = Paginator(mascotas, 20)
    page = request.GET.get('page')
    try:
        mascotas_paginadas = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        mascotas_paginadas = paginator.page(1)
    
    context = {
        'form': form,
        'mascotas': mascotas_paginadas,
        'total_original': total_original,
        'total_mascotas': total_mascotas,
        'filtros_aplicados': filtros_aplicados,
        'estadisticas_por_estado': estadisticas_por_estado,
        'estadisticas_por_categoria': estadisticas_por_categoria,
        'estadisticas_por_tipo': estadisticas_por_tipo,
        'estadisticas_por_sexo': estadisticas_por_sexo,
        'estadisticas_por_tamaño': estadisticas_por_tamaño,
        'mascotas_disponibles': mascotas_disponibles,
        'mascotas_en_proceso': mascotas_en_proceso,
        'mascotas_adoptadas': mascotas_adoptadas,
        'mascotas_esterilizadas': mascotas_esterilizadas,
        'mascotas_vacunadas': mascotas_vacunadas,
        'mascotas_con_microchip': mascotas_con_microchip,
        'promedio_edad': round(promedio_edad, 1),
        'promedio_peso': round(promedio_peso, 1),
        'mascotas_populares': mascotas_populares,
        'mascotas_antiguas': mascotas_antiguas,
    }
    return render(request, 'adopcion/busqueda_mascotas_avanzada.html', context)

@admin_email_required
def busqueda_multiple_donantes(request):
    """Vista para búsqueda múltiple de donantes con filtros avanzados"""
    
    # Obtener parámetros de filtro
    nombre_filter = request.GET.get('nombre', '')
    email_filter = request.GET.get('email', '')
    tipo_donacion_filter = request.GET.get('tipo_donacion', '')
    estado_filter = request.GET.get('estado_donacion', '')
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    monto_min = request.GET.get('monto_min', '')
    monto_max = request.GET.get('monto_max', '')
    frecuencia_filter = request.GET.get('frecuencia', '')
    
    # Query base
    donaciones = Donacion.objects.all().order_by('-fecha_donacion')
    
    # Aplicar filtros
    if nombre_filter:
        donaciones = donaciones.filter(
            Q(nombre_donante__icontains=nombre_filter) |
            Q(apellido_donante__icontains=nombre_filter)
        )
    
    if email_filter:
        donaciones = donaciones.filter(email_donante__icontains=email_filter)
    
    if tipo_donacion_filter:
        donaciones = donaciones.filter(tipo_donacion=tipo_donacion_filter)
    
    if estado_filter:
        donaciones = donaciones.filter(estado_donacion=estado_filter)
    
    if frecuencia_filter:
        donaciones = donaciones.filter(frecuencia=frecuencia_filter)
    
    if fecha_inicio:
        donaciones = donaciones.filter(fecha_donacion__date__gte=fecha_inicio)
    
    if fecha_fin:
        donaciones = donaciones.filter(fecha_donacion__date__lte=fecha_fin)
    
    if monto_min:
        donaciones = donaciones.filter(monto__gte=monto_min)
    
    if monto_max:
        donaciones = donaciones.filter(monto__lte=monto_max)
    
    # Estadísticas
    total_donaciones = donaciones.count()
    total_valor = sum(donacion.get_valor_total() for donacion in donaciones)
    
    # Estadísticas por tipo de donación
    estadisticas_por_tipo = {}
    for tipo_choice in Donacion.TIPO_DONACION_CHOICES:
        count = donaciones.filter(tipo_donacion=tipo_choice[0]).count()
        if count > 0:
            estadisticas_por_tipo[tipo_choice[1]] = count
    
    # Estadísticas por estado
    estadisticas_por_estado = {}
    for estado_choice in Donacion.objects.values_list('estado_donacion', flat=True).distinct():
        count = donaciones.filter(estado_donacion=estado_choice).count()
        if count > 0:
            estadisticas_por_estado[estado_choice] = count
    
    # Estadísticas por frecuencia
    estadisticas_por_frecuencia = {}
    for frecuencia_choice in Donacion.FRECUENCIA_CHOICES:
        count = donaciones.filter(frecuencia=frecuencia_choice[0]).count()
        if count > 0:
            estadisticas_por_frecuencia[frecuencia_choice[1]] = count
    
    # Paginación
    paginator = Paginator(donaciones, 20)
    page = request.GET.get('page')
    try:
        donaciones_paginadas = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        donaciones_paginadas = paginator.page(1)
    
    context = {
        'donaciones': donaciones_paginadas,
        'total_donaciones': total_donaciones,
        'total_valor': total_valor,
        'estadisticas_por_tipo': estadisticas_por_tipo,
        'estadisticas_por_estado': estadisticas_por_estado,
        'estadisticas_por_frecuencia': estadisticas_por_frecuencia,
        'filtros_activos': {
            'nombre': nombre_filter,
            'email': email_filter,
            'tipo_donacion': tipo_donacion_filter,
            'estado_donacion': estado_filter,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'monto_min': monto_min,
            'monto_max': monto_max,
            'frecuencia': frecuencia_filter,
        }
    }
    
    return render(request, 'adopcion/busqueda_multiple_donantes.html', context)

def login_view(request):
    """Vista personalizada de login que genera notificaciones"""
    if request.user.is_authenticated:
        return redirect('inicio')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                # Crear notificación de inicio de sesión
                crear_notificaciones_inicio_sesion(user)
                messages.success(request, f'¡Bienvenido de vuelta, {user.nombre}!')
                return redirect('inicio')
    else:
        form = AuthenticationForm()
    
    return render(request, 'registration/login.html', {'form': form})

def aprobar_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(SolicitudAdopcion, id=solicitud_id)
    solicitud.estado_solicitud = 'aprobada'
    solicitud.save()
    crear_notificaciones_solicitud(solicitud, 'aprobada')
    return redirect('detalle_solicitud', solicitud_id=solicitud_id)

def rechazar_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(SolicitudAdopcion, id=solicitud_id)
    solicitud.estado_solicitud = 'rechazada'
    solicitud.save()
    crear_notificaciones_solicitud(solicitud, 'rechazada')
    return redirect('detalle_solicitud', solicitud_id=solicitud_id)

@admin_email_required
def busqueda_multiple_donaciones(request):
    """Vista para búsqueda múltiple de donaciones en el panel de administración"""
    form = BusquedaDonacionesForm(request.GET)
    donaciones = Donacion.objects.all()
    
    if form.is_valid():
        # Aplicar filtros
        nombre = form.cleaned_data.get('nombre')
        apellido = form.cleaned_data.get('apellido')
        email = form.cleaned_data.get('email')
        tipo_donacion = form.cleaned_data.get('tipo_donacion')
        categoria = form.cleaned_data.get('categoria')
        frecuencia = form.cleaned_data.get('frecuencia')
        estado_donacion = form.cleaned_data.get('estado_donacion')
        fecha_desde = form.cleaned_data.get('fecha_desde')
        fecha_hasta = form.cleaned_data.get('fecha_hasta')
        monto_min = form.cleaned_data.get('monto_min')
        monto_max = form.cleaned_data.get('monto_max')
        anonimo = form.cleaned_data.get('anonimo')
        
        # Construir consulta
        if nombre:
            donaciones = donaciones.filter(nombre_donante__icontains=nombre)
        if apellido:
            donaciones = donaciones.filter(apellido_donante__icontains=apellido)
        if email:
            donaciones = donaciones.filter(email_donante__icontains=email)
        if tipo_donacion:
            donaciones = donaciones.filter(tipo_donacion=tipo_donacion)
        if categoria:
            donaciones = donaciones.filter(categoria_insumo=categoria)
        if frecuencia:
            donaciones = donaciones.filter(frecuencia=frecuencia)
        if estado_donacion:
            donaciones = donaciones.filter(estado_donacion=estado_donacion)
        if fecha_desde:
            donaciones = donaciones.filter(fecha_donacion__date__gte=fecha_desde)
        if fecha_hasta:
            donaciones = donaciones.filter(fecha_donacion__date__lte=fecha_hasta)
        if monto_min:
            donaciones = donaciones.filter(monto__gte=monto_min)
        if monto_max:
            donaciones = donaciones.filter(monto__lte=monto_max)
        if anonimo:
            donaciones = donaciones.filter(anonimo=anonimo == 'True')
    
    # Ordenar por fecha más reciente
    donaciones = donaciones.order_by('-fecha_donacion')
    
    # Paginación
    paginator = Paginator(donaciones, 20)
    page = request.GET.get('page')
    try:
        donaciones_paginadas = paginator.page(page)
    except PageNotAnInteger:
        donaciones_paginadas = paginator.page(1)
    except EmptyPage:
        donaciones_paginadas = paginator.page(paginator.num_pages)
    
    # Estadísticas
    total_donaciones = donaciones.count()
    total_monto = donaciones.aggregate(total=Sum('monto'))['total'] or 0
    donaciones_confirmadas = donaciones.filter(estado_donacion='confirmada').count()
    donaciones_pendientes = donaciones.filter(estado_donacion='pendiente').count()
    
    context = {
        'form': form,
        'donaciones': donaciones_paginadas,
        'total_donaciones': total_donaciones,
        'total_monto': total_monto,
        'donaciones_confirmadas': donaciones_confirmadas,
        'donaciones_pendientes': donaciones_pendientes,
    }
    
    return render(request, 'adopcion/busqueda_multiple_donaciones.html', context)
