from django.core.management.base import BaseCommand
from django.utils import timezone
from adopcion.models import Usuario, SolicitudAdopcion, Donacion, Notificacion, Mascota
from adopcion.views import crear_notificaciones_solicitudes_pendientes, crear_notificaciones_donaciones_recientes
from datetime import timedelta

class Command(BaseCommand):
    help = 'Genera notificaciones automáticas para solicitudes pendientes y donaciones recientes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tipo',
            type=str,
            choices=['solicitudes', 'donaciones', 'todas'],
            default='todas',
            help='Tipo de notificaciones a generar'
        )
        parser.add_argument(
            '--usuarios',
            type=str,
            help='Usuarios específicos para notificar (separados por coma)'
        )

    def handle(self, *args, **options):
        tipo = options['tipo']
        usuarios_especificos = options['usuarios']
        
        self.stdout.write(
            self.style.SUCCESS(f'Iniciando generación de notificaciones automáticas - Tipo: {tipo}')
        )
        
        # Filtrar usuarios si se especifican
        if usuarios_especificos:
            usernames = [u.strip() for u in usuarios_especificos.split(',')]
            usuarios = Usuario.objects.filter(username__in=usernames)
            self.stdout.write(f'Notificando a usuarios específicos: {usernames}')
        else:
            usuarios = Usuario.objects.all()
        
        notificaciones_creadas = 0
        
        if tipo in ['solicitudes', 'todas']:
            # Generar notificaciones de solicitudes pendientes para administradores
            solicitudes_pendientes = SolicitudAdopcion.objects.filter(estado_solicitud='pendiente').count()
            
            if solicitudes_pendientes > 0:
                administradores = usuarios.filter(rol='administrador')
                for admin in administradores:
                    # Verificar si ya existe una notificación similar reciente
                    notificacion_reciente = Notificacion.objects.filter(
                        usuario=admin,
                        tipo='recordatorio_admin',
                        fecha_creacion__gte=timezone.now() - timedelta(hours=6)
                    ).first()
                    
                    if not notificacion_reciente:
                        from adopcion.views import crear_notificacion
                        crear_notificacion(
                            usuario=admin,
                            tipo='recordatorio_admin',
                            titulo=f'Recordatorio: {solicitudes_pendientes} solicitudes pendientes',
                            mensaje=f'Hay {solicitudes_pendientes} solicitudes de adopción pendientes de revisión. Por favor, revisa el panel de administración.'
                        )
                        notificaciones_creadas += 1
                        self.stdout.write(f'Notificación de solicitudes pendientes creada para {admin.username}')
        
        if tipo in ['donaciones', 'todas']:
            # Generar notificaciones de donaciones recientes para administradores
            donaciones_recientes = Donacion.objects.filter(
                fecha_donacion__gte=timezone.now() - timedelta(days=1)
            ).count()
            
            if donaciones_recientes > 0:
                administradores = usuarios.filter(rol='administrador')
                for admin in administradores:
                    # Verificar si ya existe una notificación similar reciente
                    notificacion_reciente = Notificacion.objects.filter(
                        usuario=admin,
                        tipo='resumen_donaciones_admin',
                        fecha_creacion__gte=timezone.now() - timedelta(hours=12)
                    ).first()
                    
                    if not notificacion_reciente:
                        from adopcion.views import crear_notificacion
                        crear_notificacion(
                            usuario=admin,
                            tipo='resumen_donaciones_admin',
                            titulo=f'Resumen: {donaciones_recientes} donaciones en las últimas 24h',
                            mensaje=f'Se han recibido {donaciones_recientes} donaciones en las últimas 24 horas. Revisa el panel de administración para más detalles.'
                        )
                        notificaciones_creadas += 1
                        self.stdout.write(f'Notificación de donaciones recientes creada para {admin.username}')
        
        # Notificaciones especiales para usuarios regulares
        if tipo == 'todas' and not usuarios_especificos:
            # Notificar a usuarios sobre mascotas similares a sus favoritos
            usuarios_con_favoritos = usuarios.filter(rol='usuario', favoritos__isnull=False).distinct()
            
            for usuario in usuarios_con_favoritos:
                # Obtener tipos de mascotas favoritas del usuario
                tipos_favoritos = usuario.favoritos.values_list('mascota__tipo', flat=True).distinct()
                
                # Buscar mascotas nuevas del mismo tipo
                mascotas_nuevas = []
                for tipo in tipos_favoritos:
                    nuevas = Mascota.objects.filter(
                        tipo=tipo,
                        estado_adopcion='disponible',
                        fecha_ingreso__gte=timezone.now().date() - timedelta(days=7)
                    ).exclude(
                        seguidores__usuario=usuario
                    )[:3]
                    mascotas_nuevas.extend(nuevas)
                
                if mascotas_nuevas:
                    # Verificar si ya existe una notificación similar reciente
                    notificacion_reciente = Notificacion.objects.filter(
                        usuario=usuario,
                        tipo='nueva_mascota_similar',
                        fecha_creacion__gte=timezone.now() - timedelta(days=1)
                    ).first()
                    
                    if not notificacion_reciente:
                        from adopcion.views import crear_notificacion
                        nombres_mascotas = ', '.join([m.nombre for m in mascotas_nuevas[:2]])
                        crear_notificacion(
                            usuario=usuario,
                            tipo='nueva_mascota_similar',
                            titulo=f'Nuevas mascotas disponibles - {nombres_mascotas}',
                            mensaje=f'¡Hola {usuario.nombre}! Tenemos nuevas mascotas que podrían interesarte: {nombres_mascotas}. ¡Ven a conocerlas!'
                        )
                        notificaciones_creadas += 1
                        self.stdout.write(f'Notificación de mascotas similares creada para {usuario.username}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Proceso completado. {notificaciones_creadas} notificaciones creadas.')
        ) 