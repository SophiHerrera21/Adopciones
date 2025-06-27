from django.core.management.base import BaseCommand
from django.utils import timezone
from adopcion.models import Usuario, Mascota, Donacion, SolicitudAdopcion, Favorito, Notificacion, CategoriaDonacion, CitaPreAdopcion
from django.contrib.auth.hashers import make_password
import random
import os
from datetime import timedelta

NOMBRES = [
    "Luna", "Max", "Simba", "Nala", "Rocky", "Cleo", "Misha", "Buddy", "Frida", "Zeus", "Toby", "Salem", "Bruno", "Coco", "Oliver", "Nina", "Thor", "Milo", "Maya", "Rex", "Chispa", "Griselo", "Lia", "Gala", "Sasha", "Dante", "Milo", "Lia", "Gala", "Nina"
]
RAZAS_PERRO = ["Labrador", "Golden Retriever", "Pastor Alemán", "Bulldog", "Beagle", "Poodle", "Criollo", "Boxer", "Chihuahua", "Pug", "Husky"]
RAZAS_GATO = ["Siamés", "Persa", "Maine Coon", "Bengala", "Criollo", "Ragdoll", "British Shorthair", "Sphynx", "Abyssinian", "Azul Ruso"]
CATEGORIAS_MASCOTA = ["cachorro", "joven", "adulto", "senior", "especial", "urgente", "rescatado", "recuperacion", "socializacion"]
ESTADOS = ["disponible", "en_proceso", "adoptado", "no_disponible"]
SEXO = ["macho", "hembra"]
TIPO = ["perro", "gato"]

# Selección manual de fotos reales de perros y gatos (máximo 30)
FOTOS_REALES = [
    'black_cat.jpg', 'oliver_30.jpg', 'salem_29.jpg', 'nala_28.jpg', 'luna_27.jpg', 'misha_26.jpg', 'buddy_25.jpg',
    'rex_24.jpg', 'coco_22.jpg', 'bruno_21.jpg', 'max_20.jpg', 'toby_19.jpg', 'zeus_18.jpg', 'rocky_16.jpg',
    'misha_15.jpg', 'thor_14.jpg', 'zeus_13.jpg', 'toby_11.jpg', 'simba_10_tgC3zru.jpg', 'cleo_9.jpg',
    'rocky_7.jpg', 'nala_6.jpg', 'oliver_5.jpg', 'griselo_4.jpg', 'bruno_3.jpg', 'salem_1.jpg', 'frida_7.jpg',
    'toby_6.jpg', 'nala_5.jpg', 'zeus_2.jpg', 'thor_1.jpg'
]

class Command(BaseCommand):
    help = 'Limpia y carga datos de prueba: solo mascotas reales (perros y gatos) con fotos auténticas, máximo 30.'

    def handle(self, *args, **kwargs):
        self.limpiar_datos()
        self.cargar_datos_reales()

    def limpiar_datos(self):
        CitaPreAdopcion.objects.all().delete()
        Favorito.objects.all().delete()
        Notificacion.objects.all().delete()
        SolicitudAdopcion.objects.all().delete()
        Donacion.objects.all().delete()
        Mascota.objects.all().delete()
        Usuario.objects.filter(username__startswith='usuario').delete()
        Usuario.objects.filter(username__startswith='admin').delete()
        self.stdout.write(self.style.WARNING('Datos de prueba eliminados.'))

    def cargar_datos_reales(self):
        # Obtener categorías de donación existentes
        categorias_donacion = list(CategoriaDonacion.objects.all())
        if not categorias_donacion:
            # Crear categorías básicas si no existen
            categorias_basicas = ['Alimento', 'Medicinas', 'Juguetes', 'Accesorios', 'Limpieza']
            for cat in categorias_basicas:
                CategoriaDonacion.objects.get_or_create(nombre=cat)
            categorias_donacion = list(CategoriaDonacion.objects.all())
        
        # Crear administradores
        admins = []
        for i in range(3):
            admin, _ = Usuario.objects.get_or_create(
                username=f"admin{i+1}",
                defaults={
                    'nombre': f"Admin{i+1}",
                    'apellido': f"Prueba",
                    'email': f"admin{i+1}@mail.com",
                    'telefono': f"30000000{i+1}",
                    'rol': 'administrador',
                    'password': make_password('test123')
                }
            )
            admins.append(admin)
        self.stdout.write(self.style.SUCCESS(f"Creados {len(admins)} administradores"))

        # Crear usuarios normales
        usuarios = []
        for i in range(10):
            user, _ = Usuario.objects.get_or_create(
                username=f"usuario{i+1}",
                defaults={
                    'nombre': f"Usuario{i+1}",
                    'apellido': f"Demo",
                    'email': f"usuario{i+1}@mail.com",
                    'telefono': f"31000000{i+1}",
                    'rol': 'usuario',
                    'password': make_password('test123')
                }
            )
            usuarios.append(user)
        self.stdout.write(self.style.SUCCESS(f"Creados {len(usuarios)} usuarios normales"))

        # Crear mascotas solo con fotos reales de perros y gatos, sin repetir y máximo 30
        mascotas = []
        fotos = FOTOS_REALES[:30]
        random.shuffle(fotos)
        for i, foto in enumerate(fotos):
            es_gato = any(gato in foto.lower() for gato in ['luna', 'cleo', 'misha', 'nala', 'salem', 'chispa', 'griselo', 'black_cat', 'frida'])
            tipo = "gato" if es_gato else "perro"
            nombre = NOMBRES[i % len(NOMBRES)]
            sexo = random.choice(SEXO)
            estado = random.choice(ESTADOS)
            categoria = random.choice(CATEGORIAS_MASCOTA)
            raza = random.choice(RAZAS_GATO if tipo=="gato" else RAZAS_PERRO)
            edad_meses = random.randint(2, 120)
            peso = round(random.uniform(2, 40), 1) if tipo=="perro" else round(random.uniform(1, 8), 1)
            admin_reg = random.choice(admins)
            mascota, _ = Mascota.objects.get_or_create(
                nombre=nombre+str(i),
                tipo=tipo,
                sexo=sexo,
                categoria=categoria,
                raza=raza,
                edad_aproximada_meses=edad_meses,
                peso=peso,
                color=random.choice(["Negro", "Blanco", "Marrón", "Gris", "Atigrado", "Naranja", "Tricolor"]),
                descripcion=f"{nombre} es un {tipo} muy especial y cariñoso.",
                personalidad=random.choice(["Juguetón", "Tranquilo", "Cariñoso", "Curioso", "Protector", "Independiente"]),
                estado_salud="Bueno",
                vacunas_completas=True,
                esterilizado=random.choice([True, False]),
                microchip=random.choice([True, False]),
                estado_adopcion=estado,
                fecha_ingreso=timezone.now().date() - timedelta(days=random.randint(10, 400)),
                imagen_principal=f"mascotas/{foto}",
                id_admin_registro=admin_reg
            )
            mascotas.append(mascota)
        self.stdout.write(self.style.SUCCESS(f"Creadas {len(mascotas)} mascotas reales (perros y gatos) con fotos auténticas"))

        # Crear donaciones variadas con diferentes categorías
        tipos_donacion = ['monetaria', 'insumos', 'servicios', 'especie']
        
        for i, user in enumerate(usuarios):
            # Crear múltiples donaciones por usuario con diferentes tipos
            for j in range(random.randint(1, 3)):
                tipo_don = tipos_donacion[j % len(tipos_donacion)]
                
                donacion = Donacion.objects.create(
                    usuario=user,
                    nombre_donante=user.nombre,
                    apellido_donante=user.apellido,
                    email_donante=user.email,
                    telefono_donante=user.telefono,
                    tipo_identificacion='cc',
                    numero_identificacion=f"10{random.randint(100000,999999)}",
                    direccion_donante=f"Calle {random.randint(1,99)} # {random.randint(1,99)}-{random.randint(1,99)}",
                    ciudad_donante="Ciudad Demo",
                    tipo_donacion=tipo_don,
                    frecuencia=random.choice(['unica','mensual','anual']),
                    monto=random.randint(10000, 500000) if tipo_don == 'monetaria' else 0,
                    medio_pago=random.choice(['pse','tarjeta_credito','efectivo']) if tipo_don == 'monetaria' else None,
                    categoria_insumo=random.choice(categorias_donacion) if tipo_don == 'insumos' else None,
                    descripcion_insumo="Alimento premium, juguetes, medicinas" if tipo_don == 'insumos' else "",
                    cantidad_insumo=random.randint(1,10) if tipo_don == 'insumos' else 0,
                    unidad_medida="unidades" if tipo_don == 'insumos' else "",
                    tipo_servicio="Paseo, cuidado, transporte" if tipo_don == 'servicios' else "",
                    descripcion_servicio="Paseo de mascotas semanal, cuidado en vacaciones" if tipo_don == 'servicios' else "",
                    horas_servicio=random.randint(1,5) if tipo_don == 'servicios' else 0,
                    fecha_servicio=timezone.now().date() + timedelta(days=random.randint(1,30)) if tipo_don == 'servicios' else None,
                    descripcion_especie="Cama, cobijas, platos, transportadora" if tipo_don == 'especie' else "",
                    valor_estimado=random.randint(5000, 100000) if tipo_don == 'especie' else 0,
                    motivo_donacion="Ayudar a los peludos necesitados",
                    anonimo=random.choice([True, False]),
                    recibir_informacion=True,
                    estado_donacion=random.choice(['pendiente','confirmada','rechazada']),
                    comentarios_admin="Donación de prueba variada",
                    fecha_confirmacion=timezone.now() if random.choice([True, False]) else None,
                    admin_confirmador=random.choice(admins) if random.choice([True, False]) else None
                )
        self.stdout.write(self.style.SUCCESS(f"Creadas donaciones variadas con diferentes categorías"))

        # Crear solicitudes de adopción
        solicitudes_creadas = []
        for user in usuarios:
            mascota = random.choice(mascotas)
            solicitud = SolicitudAdopcion.objects.create(
                usuario=user,
                mascota=mascota,
                vivienda=random.choice(['casa','apartamento']),
                es_propia=random.choice([True, False]),
                tiene_patio=random.choice([True, False]),
                tamano_patio=random.choice(['pequeno','mediano','grande','no_aplica']),
                adultos_en_casa=random.randint(1,3),
                ninos_en_casa=random.randint(0,2),
                edades_ninos="5, 8" if random.choice([True, False]) else "",
                tuvo_mascotas=random.choice([True, False]),
                experiencia_mascotas="He tenido perros y gatos antes.",
                otras_mascotas="Ninguna" if random.choice([True, False]) else "Pez, ave",
                tiempo_diario="2 horas",
                todos_deacuerdo=True,
                cuidador_principal=user.nombre,
                plan_vacaciones="Dejar con familiar",
                ingreso_aproximado="$2.000.000",
                presupuesto_mensual_mascota="$100.000",
                tiene_veterinario=random.choice([True, False]),
                nombre_veterinario="Dr. Animal",
                motivo_adopcion="Quiero darle un hogar a un peludo.",
                manejo_comportamiento="Buscar ayuda profesional",
                compromiso_largo_plazo=True,
                preferencias_mascota="Tranquilo, mediano",
                comentario_extra="Ninguno",
                estado_solicitud=random.choice(['pendiente','aprobada','rechazada','en_revision']),
                comentarios_admin="Solicitud de prueba",
                fecha_solicitud=timezone.now() - timedelta(days=random.randint(1,30)),
                fecha_respuesta=timezone.now(),
                id_admin_revisor=random.choice(admins)
            )
            solicitudes_creadas.append(solicitud)
        self.stdout.write(self.style.SUCCESS(f"Creadas solicitudes de adopción"))

        # Crear citas de pre-adopción
        for i in range(len(solicitudes_creadas) // 2):  # Citas para la mitad de solicitudes
            solicitud = solicitudes_creadas[i]
            
            CitaPreAdopcion.objects.create(
                solicitud=solicitud,
                fecha_cita=timezone.now() + timedelta(days=random.randint(1, 14), hours=random.randint(9, 17)),
                duracion_minutos=30,
                lugar="Sede principal Luna & Lía",
                estado=random.choice(['programada', 'confirmada', 'cancelada', 'completada']),
                observaciones_admin="Cita de pre-adopción para conocer a la mascota",
                observaciones_usuario=""
            )
        self.stdout.write(self.style.SUCCESS(f"Creadas citas de pre-adopción"))

        # Crear favoritos
        for user in usuarios:
            fav_mascota = random.choice(mascotas)
            Favorito.objects.get_or_create(usuario=user, mascota=fav_mascota)
        self.stdout.write(self.style.SUCCESS(f"Creados favoritos"))

        # Crear notificaciones variadas
        for user in usuarios:
            Notificacion.objects.create(
                usuario=user,
                tipo='general',
                titulo='¡Bienvenido a Luna & Lía!',
                mensaje='Gracias por registrarte y apoyar la adopción responsable.',
            )
            
            # Notificación adicional para algunos usuarios
            if random.choice([True, False]):
                Notificacion.objects.create(
                    usuario=user,
                    tipo='solicitud',
                    titulo='Nueva solicitud de adopción',
                    mensaje='Tu solicitud de adopción ha sido recibida y está en revisión.',
                )
        self.stdout.write(self.style.SUCCESS(f"Creadas notificaciones variadas"))

        self.stdout.write(self.style.SUCCESS("¡Datos de prueba completos cargados exitosamente!"))
        self.stdout.write(self.style.SUCCESS(f"Total: {len(mascotas)} mascotas (perros y gatos), {len(usuarios)} usuarios, donaciones variadas, citas pre-adopción")) 