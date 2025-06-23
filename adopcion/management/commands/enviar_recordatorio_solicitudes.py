from django.core.management.base import BaseCommand
from django.utils import timezone
from adopcion.models import SolicitudAdopcion
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

class Command(BaseCommand):
    help = 'Envía correos de seguimiento a solicitudes de adopción pendientes por más de 7 días'

    def handle(self, *args, **kwargs):
        hoy = timezone.now()
        solicitudes = SolicitudAdopcion.objects.filter(
            estado_solicitud__in=['pendiente', 'en_revision'],
            fecha_respuesta__isnull=True
        )
        count = 0
        for solicitud in solicitudes:
            dias_pendiente = (hoy - solicitud.fecha_solicitud).days
            if dias_pendiente >= 7:
                context = {'solicitud': solicitud}
                subject = f'Seguimos revisando tu solicitud de adopción de {solicitud.mascota.nombre}'
                html_message = render_to_string('emails/seguimiento_solicitud.html', context)
                plain_message = render_to_string('emails/seguimiento_solicitud.txt', context)
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [solicitud.usuario.email],
                    html_message=html_message,
                    fail_silently=False
                )
                count += 1
        self.stdout.write(self.style.SUCCESS(f'Se enviaron {count} correos de seguimiento.')) 