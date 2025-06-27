from django.core.management.base import BaseCommand
from adopcion.models import Usuario, Notificacion
from django.utils import timezone

class Command(BaseCommand):
    help = 'Crear una notificación personalizada para un usuario específico'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nombre de usuario')
        parser.add_argument('titulo', type=str, help='Título de la notificación')
        parser.add_argument('mensaje', type=str, help='Mensaje de la notificación')
        parser.add_argument('--tipo', type=str, default='general', help='Tipo de notificación (default: general)')

    def handle(self, *args, **options):
        username = options['username']
        titulo = options['titulo']
        mensaje = options['mensaje']
        tipo = options['tipo']

        try:
            # Buscar el usuario
            usuario = Usuario.objects.get(username=username)
            
            # Crear la notificación
            notificacion = Notificacion.objects.create(
                usuario=usuario,
                tipo=tipo,
                titulo=titulo,
                mensaje=mensaje,
                fecha_creacion=timezone.now()
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Notificación creada exitosamente para {usuario.get_full_name()} ({username})\n'
                    f'📝 Título: {titulo}\n'
                    f'💬 Mensaje: {mensaje}\n'
                    f'📅 Fecha: {notificacion.fecha_creacion.strftime("%d/%m/%Y %H:%M")}'
                )
            )
            
        except Usuario.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: No se encontró el usuario "{username}"')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al crear la notificación: {str(e)}')
            ) 