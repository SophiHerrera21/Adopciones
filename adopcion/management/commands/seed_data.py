import requests
import os
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from adopcion.models import Mascota, Donacion, SolicitudAdopcion, Usuario, CategoriaDonacion
import random
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

# APIs especializadas para fotos reales y de alta calidad
DOG_API_URL = "https://api.thedogapi.com/v1/images/search"
CAT_API_URL = "https://api.thecatapi.com/v1/images/search"

def get_image_url(api_url):
    """Obtiene una URL de imagen aleatoria de la API especificada."""
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        if data and data[0].get('url'):
            return data[0]['url']
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con la API de imágenes: {e}")
    return None

class Command(BaseCommand):
    help = 'Puebla la base de datos con datos completos de prueba incluyendo mascotas, donaciones, solicitudes y usuarios.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('--- Iniciando población completa de la base de datos ---'))
        
        # Limpiar datos existentes
        self.stdout.write('Limpiando datos existentes...')
        Mascota.objects.all().delete()
        Donacion.objects.all().delete()
        SolicitudAdopcion.objects.all().delete()
        Usuario.objects.filter(is_superuser=False).delete()
        self.stdout.write(self.style.SUCCESS('Datos limpiados exitosamente.'))

        # Crear usuarios de prueba
        self.crear_usuarios()
        
        # Crear mascotas con diferentes estados
        self.crear_mascotas()
        
        # Crear donaciones variadas
        self.crear_donaciones()
        
        # Crear solicitudes de adopción
        self.crear_solicitudes_adopcion()
        
        self.stdout.write(self.style.SUCCESS('\n--- ¡Base de datos poblada exitosamente! ---'))
        self.stdout.write(self.style.SUCCESS('Datos creados:'))
        self.stdout.write(f'  - {Usuario.objects.count()} usuarios')
        self.stdout.write(f'  - {Mascota.objects.count()} mascotas')
        self.stdout.write(f'  - {Donacion.objects.count()} donaciones')
        self.stdout.write(f'  - {SolicitudAdopcion.objects.count()} solicitudes de adopción')

    def crear_usuarios(self):
        """Crear usuarios de prueba con diferentes roles."""
        usuarios_data = [
            {'username': 'maria_garcia', 'email': 'maria.garcia@email.com', 'nombre': 'María', 'apellido': 'García', 'password': 'maria12345'},
            {'username': 'carlos_rodriguez', 'email': 'carlos.rodriguez@email.com', 'nombre': 'Carlos', 'apellido': 'Rodríguez', 'password': 'carlos12345'},
            {'username': 'ana_martinez', 'email': 'ana.martinez@email.com', 'nombre': 'Ana', 'apellido': 'Martínez', 'password': 'ana12345'},
            {'username': 'juan_lopez', 'email': 'juan.lopez@email.com', 'nombre': 'Juan', 'apellido': 'López', 'password': 'juan12345'},
            {'username': 'lucia_hernandez', 'email': 'lucia.hernandez@email.com', 'nombre': 'Lucía', 'apellido': 'Hernández', 'password': 'lucia12345'},
            {'username': 'pedro_gonzalez', 'email': 'pedro.gonzalez@email.com', 'nombre': 'Pedro', 'apellido': 'González', 'password': 'pedro12345'},
            {'username': 'carmen_ruiz', 'email': 'carmen.ruiz@email.com', 'nombre': 'Carmen', 'apellido': 'Ruiz', 'password': 'carmen12345'},
            {'username': 'diego_morales', 'email': 'diego.morales@email.com', 'nombre': 'Diego', 'apellido': 'Morales', 'password': 'diego12345'},
        ]
        
        for user_data in usuarios_data:
            try:
                usuario = Usuario.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    nombre=user_data['nombre'],
                    apellido=user_data['apellido'],
                    password=user_data['password']
                )
                self.stdout.write(f'Usuario creado: {usuario.nombre} {usuario.apellido}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creando usuario {user_data["username"]}: {e}'))

    def crear_mascotas(self):
        """Crear mascotas con diferentes estados de adopción."""
        nombres_perro = ["Rocky", "Thor", "Zeus", "Toby", "Max", "Bruno", "Coco", "Simba", "Rex", "Buddy"]
        nombres_gato = ["Misha", "Luna", "Nala", "Salem", "Oliver", "Cleo", "Griselo", "Mittens", "Shadow", "Whiskers"]
        
        # Estados de adopción para mostrar diferentes situaciones
        estados_adopcion = ['disponible'] * 6 + ['en_proceso'] * 3 + ['adoptado'] * 4 + ['no_disponible'] * 2
        
        for i, estado in enumerate(estados_adopcion):
            if i < len(nombres_perro) + len(nombres_gato):
                if i < len(nombres_perro):
                    nombre = nombres_perro[i]
                    tipo = 'perro'
                    image_url = get_image_url(DOG_API_URL)
                else:
                    nombre = nombres_gato[i - len(nombres_perro)]
                    tipo = 'gato'
                    image_url = get_image_url(CAT_API_URL)
                
                if not image_url:
                    continue
                
                try:
                    self.stdout.write(f'Creando mascota: {nombre} ({estado})')
                    
                    mascota = Mascota.objects.create(
                        nombre=nombre,
                        tipo=tipo,
                        edad_aproximada_meses=random.randint(3, 72),
                        sexo=random.choice(['macho', 'hembra']),
                        tamaño=random.choice(['pequeño', 'mediano', 'grande']),
                        estado_salud='Bueno y listo para un hogar' if estado != 'no_disponible' else 'En tratamiento médico',
                        descripcion=f'Un adorable {tipo} llamado {nombre}, lleno de energía y amor para dar.',
                        personalidad=random.choice(['Juguetón', 'Tranquilo', 'Cariñoso', 'Independiente']),
                        esterilizado=random.choice([True, False]),
                        fecha_ingreso=date.today() - timedelta(days=random.randint(5, 200)),
                        estado_adopcion=estado
                    )
                    
                    file_ext = os.path.splitext(image_url)[1].split('?')[0] or '.jpg'
                    file_name = f'{nombre.lower()}_{mascota.id}{file_ext}'
                    mascota.imagen_principal.save(file_name, ContentFile(requests.get(image_url).content), save=True)
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error creando mascota {nombre}: {e}'))

    def crear_donaciones(self):
        """Crear donaciones variadas para mostrar en reportes."""
        usuarios = list(Usuario.objects.all())
        tipos_donacion = ['monetaria'] * 8 + ['insumos'] * 7
        medios_pago = ['pse', 'tarjeta_credito', 'tarjeta_debito', 'transferencia']
        
        # Obtener categorías existentes
        categorias = list(CategoriaDonacion.objects.all())
        if not categorias:
            # Si no hay categorías, crear algunas básicas
            categorias = [
                CategoriaDonacion.objects.create(nombre='Alimentos', descripcion='Comida para mascotas'),
                CategoriaDonacion.objects.create(nombre='Medicamentos', descripcion='Medicamentos veterinarios'),
                CategoriaDonacion.objects.create(nombre='Juguetes', descripcion='Juguetes para mascotas'),
                CategoriaDonacion.objects.create(nombre='Accesorios', descripcion='Collares, correas, etc.'),
            ]
        
        montos_monetarios = [50000, 100000, 150000, 200000, 250000, 300000, 500000, 750000, 1000000]
        descripciones_insumos = [
            '10kg de concentrado premium para perros adultos',
            '5kg de comida húmeda para gatos',
            'Medicamentos antiparasitarios y vitaminas',
            'Juguetes interactivos y pelotas',
            'Camas ortopédicas y mantas limpias',
            'Shampoo y productos de higiene',
            'Collares, correas y platos de comida'
        ]
        
        for i in range(15):
            try:
                tipo = tipos_donacion[i]
                usuario = random.choice(usuarios)
                
                if tipo == 'monetaria':
                    donacion = Donacion.objects.create(
                        nombre_donante=usuario.nombre,
                        apellido_donante=usuario.apellido,
                        email_donante=usuario.email,
                        telefono_donante=f"+57 300 {random.randint(1000000, 9999999)}",
                        tipo_donacion=tipo,
                        monto=random.choice(montos_monetarios),
                        medio_pago=random.choice(medios_pago),
                        fecha_donacion=date.today() - timedelta(days=random.randint(1, 90))
                    )
                else:
                    donacion = Donacion.objects.create(
                        nombre_donante=usuario.nombre,
                        apellido_donante=usuario.apellido,
                        email_donante=usuario.email,
                        telefono_donante=f"+57 300 {random.randint(1000000, 9999999)}",
                        tipo_donacion=tipo,
                        categoria_insumo=random.choice(categorias),
                        descripcion_insumo=random.choice(descripciones_insumos),
                        fecha_donacion=date.today() - timedelta(days=random.randint(1, 90))
                    )
                
                self.stdout.write(f'Donación creada: {donacion.tipo_donacion} - {donacion.nombre_donante}')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creando donación: {e}'))

    def crear_solicitudes_adopcion(self):
        """Crear solicitudes de adopción con diferentes estados."""
        usuarios = list(Usuario.objects.all())
        mascotas_disponibles = list(Mascota.objects.filter(estado_adopcion='disponible'))
        mascotas_en_proceso = list(Mascota.objects.filter(estado_adopcion='en_proceso'))
        
        estados_solicitud = ['pendiente'] * 4 + ['aprobada'] * 3 + ['rechazada'] * 2 + ['en_revision'] * 2
        
        for i, estado in enumerate(estados_solicitud):
            try:
                usuario = random.choice(usuarios)
                
                # Asignar mascota según el estado
                if estado == 'aprobada' and mascotas_en_proceso:
                    mascota = random.choice(mascotas_en_proceso)
                elif mascotas_disponibles:
                    mascota = random.choice(mascotas_disponibles)
                else:
                    continue
                
                solicitud = SolicitudAdopcion.objects.create(
                    usuario=usuario,
                    mascota=mascota,
                    vivienda=random.choice(['casa', 'apartamento', 'finca']),
                    es_propia=random.choice([True, False]),
                    tiene_patio=random.choice([True, False]),
                    adultos_en_casa=random.randint(1, 4),
                    ninos_en_casa=random.randint(0, 3),
                    tuvo_mascotas=random.choice([True, False]),
                    tiempo_diario=random.choice(['1-2 horas', '2-4 horas', '4+ horas']),
                    todos_deacuerdo=True,
                    cuidador_principal=usuario.nombre,
                    plan_vacaciones='Buscar cuidador o llevarlo con nosotros',
                    ingreso_aproximado=random.choice(['1-2 SMLV', '2-4 SMLV', '4+ SMLV']),
                    presupuesto_mensual_mascota=random.choice(['50-100k', '100-200k', '200k+']),
                    tiene_veterinario=random.choice([True, False]),
                    motivo_adopcion='Quiero darle un hogar amoroso a una mascota que lo necesite',
                    manejo_comportamiento='Buscaría ayuda profesional si fuera necesario',
                    compromiso_largo_plazo=True,
                    estado_solicitud=estado
                )
                
                self.stdout.write(f'Solicitud creada: {usuario.nombre} - {mascota.nombre} ({estado})')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creando solicitud: {e}'))

    def enviar_recordatorio_solicitudes(self):
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
                    # Enviar correo de seguimiento
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