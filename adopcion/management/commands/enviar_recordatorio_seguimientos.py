from django.core.management.base import BaseCommand
from django.utils import timezone
from adopcion.models import SeguimientoMascota, Usuario
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

class Command(BaseCommand):
    help = 'Envía correos de recordatorio de cita de seguimiento a adoptante y administradores.'

    def handle(self, *args, **kwargs):
        hoy = timezone.now().date()
        seguimientos = SeguimientoMascota.objects.filter(proxima_cita=hoy, completada=False)
        admins = Usuario.objects.filter(rol='administrador').values_list('email', flat=True)
        count = 0
        for seguimiento in seguimientos:
            context = {'seguimiento': seguimiento}
            subject = f'Recordatorio de cita de seguimiento para {seguimiento.mascota.nombre} (Cita {seguimiento.numero_cita})'
            html_message = render_to_string('emails/recordatorio_seguimiento.html', context)
            plain_message = render_to_string('emails/recordatorio_seguimiento.txt', context)
            # Enviar al adoptante
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [seguimiento.adoptante.email],
                html_message=html_message,
                fail_silently=False
            )
            # Enviar a todos los administradores
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                list(admins),
                html_message=html_message,
                fail_silently=False
            )
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Se enviaron {count} recordatorios de seguimiento.')) 