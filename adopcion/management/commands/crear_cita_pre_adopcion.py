from django.core.management.base import BaseCommand
from django.utils import timezone
from adopcion.models import Usuario, SolicitudAdopcion, CitaPreAdopcion, Mascota
from adopcion.views import crear_notificaciones_cita
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Crea citas de pre-adopción y genera notificaciones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--solicitud_id',
            type=int,
            help='ID de la solicitud para crear la cita'
        )
        parser.add_argument(
            '--fecha',
            type=str,
            help='Fecha de la cita (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--hora',
            type=str,
            help='Hora de la cita (HH:MM)'
        )
        parser.add_argument(
            '--usuario',
            type=str,
            help='Username del usuario para crear cita'
        )
        parser.add_argument(
            '--mascota',
            type=str,
            help='Nombre de la mascota para crear cita'
        )

    def handle(self, *args, **options):
        solicitud_id = options['solicitud_id']
        fecha_str = options['fecha']
        hora_str = options['hora']
        usuario_username = options['usuario']
        mascota_nombre = options['mascota']
        
        # Buscar solicitud por diferentes criterios
        solicitud = None
        
        if solicitud_id:
            try:
                solicitud = SolicitudAdopcion.objects.get(id=solicitud_id)
            except SolicitudAdopcion.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'No se encontró solicitud con ID {solicitud_id}')
                )
                return
        
        elif usuario_username and mascota_nombre:
            try:
                usuario = Usuario.objects.get(username=usuario_username)
                mascota = Mascota.objects.get(nombre__iexact=mascota_nombre)
                solicitud = SolicitudAdopcion.objects.get(
                    usuario=usuario,
                    mascota=mascota,
                    estado_solicitud='pendiente'
                )
            except (Usuario.DoesNotExist, Mascota.DoesNotExist, SolicitudAdopcion.DoesNotExist):
                self.stdout.write(
                    self.style.ERROR(f'No se encontró solicitud para usuario {usuario_username} y mascota {mascota_nombre}')
                )
                return
        
        else:
            # Mostrar solicitudes pendientes disponibles
            solicitudes_pendientes = SolicitudAdopcion.objects.filter(
                estado_solicitud='pendiente'
            ).select_related('usuario', 'mascota')
            
            if not solicitudes_pendientes.exists():
                self.stdout.write(
                    self.style.WARNING('No hay solicitudes pendientes para crear citas.')
                )
                return
            
            self.stdout.write('Solicitudes pendientes disponibles:')
            for sol in solicitudes_pendientes:
                self.stdout.write(f'ID: {sol.id} - Usuario: {sol.usuario.username} - Mascota: {sol.mascota.nombre}')
            
            return
        
        # Procesar fecha y hora
        if not fecha_str:
            fecha_str = (timezone.now().date() + timedelta(days=3)).strftime('%Y-%m-%d')
        
        if not hora_str:
            hora_str = '15:00'
        
        try:
            fecha_cita = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            hora_cita = datetime.strptime(hora_str, '%H:%M').time()
        except ValueError:
            self.stdout.write(
                self.style.ERROR('Formato de fecha u hora inválido. Use YYYY-MM-DD para fecha y HH:MM para hora.')
            )
            return
        
        # Crear la cita
        try:
            cita = CitaPreAdopcion.objects.create(
                solicitud=solicitud,
                fecha_cita=fecha_cita,
                hora_cita=hora_cita,
                estado_cita='programada',
                notas='Cita creada automáticamente'
            )
            
            # Crear notificaciones
            crear_notificaciones_cita(cita, 'creada')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Cita creada exitosamente:\n'
                    f'- Usuario: {solicitud.usuario.get_full_name()}\n'
                    f'- Mascota: {solicitud.mascota.nombre}\n'
                    f'- Fecha: {fecha_cita.strftime("%d/%m/%Y")}\n'
                    f'- Hora: {hora_cita.strftime("%H:%M")}\n'
                    f'- Notificaciones enviadas'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creando la cita: {e}')
            ) 