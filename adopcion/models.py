from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import random

# Modelo de Usuario Personalizado
class Usuario(AbstractUser):
    ROL_CHOICES = (
        ('usuario', 'Usuario'),
        ('administrador', 'Administrador'),
    )
    TIPO_VIVIENDA_CHOICES = (
        ('casa', 'Casa'),
        ('apartamento', 'Apartamento'),
        ('finca', 'Finca'),
    )
    
    # Eliminamos 'first_name' y 'last_name' para usar 'nombre' y 'apellido' si se prefiere
    # y los redefinimos para asegurar que no vienen del AbstractUser base.
    first_name = None
    last_name = None
    
    nombre = models.CharField(max_length=100, blank=False, null=False)
    apellido = models.CharField(max_length=100, blank=False, null=False)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    ocupacion = models.CharField(max_length=100, blank=True)
    tipo_vivienda = models.CharField(max_length=20, choices=TIPO_VIVIENDA_CHOICES, default='casa')
    tiene_experiencia_mascotas = models.BooleanField(default=False)
    rol = models.CharField(max_length=15, choices=ROL_CHOICES, default='usuario')

    def __str__(self):
        return self.username

# Modelo de Mascotas
class Mascota(models.Model):
    TIPO_CHOICES = (('perro', 'Perro'), ('gato', 'Gato'))
    SEXO_CHOICES = (('macho', 'Macho'), ('hembra', 'Hembra'))
    TAMAÑO_CHOICES = (('pequeño', 'Pequeño'), ('mediano', 'Mediano'), ('grande', 'Grande'))
    ESTADO_ADOPCION_CHOICES = (
        ('disponible', 'Disponible'),
        ('en_proceso', 'En Proceso'),
        ('adoptado', 'Adoptado'),
        ('no_disponible', 'No Disponible')
    )

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    raza = models.CharField(max_length=100, blank=True)
    edad_aproximada = models.IntegerField(
        help_text="en meses",
        validators=[
            MinValueValidator(0, message="La edad no puede ser negativa."),
            MaxValueValidator(204, message="La edad máxima es de 17 años (204 meses).")
        ]
    )
    sexo = models.CharField(max_length=10, choices=SEXO_CHOICES)
    tamaño = models.CharField(max_length=10, choices=TAMAÑO_CHOICES, default='mediano')
    peso = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        help_text="en kilogramos", 
        null=True, 
        blank=True,
        validators=[
            MinValueValidator(0.01, message="El peso debe ser mayor a 0.")
        ]
    )
    color = models.CharField(max_length=100, blank=True)
    descripcion = models.TextField(blank=True)
    personalidad = models.TextField(blank=True)
    necesidades_especiales = models.TextField(blank=True)
    estado_salud = models.TextField()
    vacunas_completas = models.BooleanField(default=False)
    esterilizado = models.BooleanField(default=False)
    microchip = models.BooleanField(default=False)
    estado_adopcion = models.CharField(max_length=15, choices=ESTADO_ADOPCION_CHOICES, default='disponible')
    fecha_ingreso = models.DateField()
    fecha_adopcion = models.DateField(null=True, blank=True)
    
    # Campo para la imagen principal
    imagen_principal = models.ImageField(upload_to='mascotas/', null=True, blank=True, help_text="Imagen principal de la mascota")

    id_admin_registro = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='mascotas_registradas')
    fecha_registro = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.nombre} ({self.tipo})"

    def get_imagen_url(self):
        """Obtiene la URL de la imagen principal o la primera foto disponible"""
        if self.imagen_principal:
            return self.imagen_principal.url
        elif self.fotos.exists():
            return self.fotos.first().url_foto.url
        else:
            return '/static/images/default-pet.png'
    
    def get_estado_display(self):
        """Obtiene el estado de adopción en formato legible"""
        return dict(self.ESTADO_ADOPCION_CHOICES).get(self.estado_adopcion, 'Desconocido')
    
    def get_tipo_display(self):
        """Obtiene el tipo de mascota en formato legible"""
        return dict(self.TIPO_CHOICES).get(self.tipo, 'Desconocido')
    
    def get_sexo_display(self):
        """Obtiene el sexo en formato legible"""
        return dict(self.SEXO_CHOICES).get(self.sexo, 'Desconocido')
    
    def get_tamaño_display(self):
        """Obtiene el tamaño en formato legible"""
        return dict(self.TAMAÑO_CHOICES).get(self.tamaño, 'Desconocido')
    
    @classmethod
    def contar_peludos_en_fundacion(cls):
        """Cuenta cuántos peludos hay actualmente en la fundación"""
        return cls.objects.filter(estado_adopcion__in=['disponible', 'en_proceso', 'en_tratamiento']).count()
    
    @classmethod
    def contar_peludos_adoptados(cls):
        """Cuenta cuántos peludos han sido adoptados"""
        return cls.objects.filter(estado_adopcion='adoptado').count()
    
    @classmethod
    def obtener_estadisticas_peludos(cls):
        """Obtiene estadísticas completas de los peludos"""
        return {
            'en_fundacion': cls.contar_peludos_en_fundacion(),
            'adoptados': cls.contar_peludos_adoptados(),
            'total': cls.objects.count(),
            'perros': cls.objects.filter(tipo='perro').count(),
            'gatos': cls.objects.filter(tipo='gato').count(),
            'disponibles': cls.objects.filter(estado_adopcion='disponible').count(),
            'en_proceso': cls.objects.filter(estado_adopcion='en_proceso').count(),
            'en_tratamiento': cls.objects.filter(estado_adopcion='en_tratamiento').count(),
        }
    
    def save(self, *args, **kwargs):
        """Sobrescribe el método save para asegurar que las imágenes se adapten correctamente"""
        # Si es una nueva mascota y no tiene fecha de ingreso, asignar la fecha actual
        if not self.pk and not self.fecha_ingreso:
            self.fecha_ingreso = timezone.now().date()
        
        super().save(*args, **kwargs)

# Modelo de Fotos de Mascotas
class FotoMascota(models.Model):
    mascota = models.ForeignKey(Mascota, on_delete=models.CASCADE, related_name='fotos')
    url_foto = models.ImageField(upload_to='mascotas_fotos/')
    es_principal = models.BooleanField(default=False)
    descripcion = models.CharField(max_length=255, blank=True)
    fecha_subida = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Foto de {self.mascota.nombre}"

# Modelo de Solicitudes de Adopción
class SolicitudAdopcion(models.Model):
    ESTADO_SOLICITUD_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('en_revision', 'En Revisión'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    )
    VIVIENDA_CHOICES = [
        ('casa', 'Casa'), ('apartamento', 'Apartamento'), ('finca', 'Finca'), ('otro', 'Otro')
    ]
    TAMAÑO_PATIO_CHOICES = [
        ('pequeno', 'Pequeño'), ('mediano', 'Mediano'), ('grande', 'Grande'), ('no_aplica', 'No aplica')
    ]

    # Relaciones clave
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='solicitudes')
    mascota = models.ForeignKey(Mascota, on_delete=models.CASCADE, related_name='solicitudes')

    # Información del formulario de pre-adopción
    vivienda = models.CharField(max_length=30, choices=VIVIENDA_CHOICES, default='casa')
    es_propia = models.BooleanField(verbose_name="¿La vivienda es propia?", default=False)
    tiene_patio = models.BooleanField(verbose_name="¿Tiene patio o terraza?", default=False)
    tamano_patio = models.CharField(max_length=20, choices=TAMAÑO_PATIO_CHOICES, default='no_aplica')
    adultos_en_casa = models.PositiveIntegerField(verbose_name="¿Cuántos adultos viven en la casa?", default=1)
    ninos_en_casa = models.PositiveIntegerField(default=0, verbose_name="¿Cuántos niños viven en la casa?")
    edades_ninos = models.TextField(blank=True, verbose_name="Edades de los niños")
    
    tuvo_mascotas = models.BooleanField(verbose_name="¿Ha tenido mascotas antes?", default=False)
    experiencia_mascotas = models.TextField(blank=True, verbose_name="Describa su experiencia con mascotas")
    otras_mascotas = models.CharField(max_length=100, blank=True, verbose_name="¿Qué otras mascotas tiene actualmente?")
    
    tiempo_diario = models.CharField(max_length=50, verbose_name="¿Cuánto tiempo diario puede dedicarle a la mascota?", default='')
    todos_deacuerdo = models.BooleanField(verbose_name="¿Todos en casa están de acuerdo con la adopción?", default=False)
    cuidador_principal = models.CharField(max_length=100, verbose_name="¿Quién será el cuidador principal?", default='')
    
    plan_vacaciones = models.TextField(verbose_name="¿Qué planes tiene para la mascota en vacaciones?", default='')
    ingreso_aproximado = models.CharField(max_length=50, verbose_name="Ingreso mensual aproximado del hogar", default='')
    presupuesto_mensual_mascota = models.CharField(max_length=50, verbose_name="Presupuesto mensual para la mascota", default='')
    
    tiene_veterinario = models.BooleanField(verbose_name="¿Tiene un veterinario de confianza?", default=False)
    nombre_veterinario = models.CharField(max_length=100, blank=True)
    
    motivo_adopcion = models.TextField(verbose_name="¿Por qué desea adoptar?", default='')
    manejo_comportamiento = models.TextField(verbose_name="¿Cómo manejaría un problema de comportamiento?", default='')
    compromiso_largo_plazo = models.BooleanField(verbose_name="¿Se compromete a cuidarlo por toda su vida? (15 años o más)", default=False)
    acepta_visitas_seguimiento = models.BooleanField(verbose_name="¿Acepta visitas de seguimiento post-adopción?", default=False)
    
    preferencias_mascota = models.TextField(blank=True, verbose_name="¿Tiene alguna preferencia sobre la mascota?")
    comentario_extra = models.TextField(blank=True, verbose_name="Comentarios adicionales")

    # Estado y seguimiento de la solicitud
    estado_solicitud = models.CharField(max_length=15, choices=ESTADO_SOLICITUD_CHOICES, default='pendiente')
    comentarios_admin = models.TextField(blank=True)
    fecha_solicitud = models.DateTimeField(default=timezone.now)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    id_admin_revisor = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitudes_revisadas')

    class Meta:
        # Evita que un usuario envíe múltiples solicitudes para la misma mascota si una ya está pendiente.
        unique_together = ('usuario', 'mascota')

# Modelo de Seguimiento Post-Adopción
class SeguimientoAdopcion(models.Model):
    ESTADO_MASCOTA_CHOICES = (
        ('excelente', 'Excelente'),
        ('bueno', 'Bueno'),
        ('regular', 'Regular'),
        ('preocupante', 'Preocupante'),
    )

    solicitud = models.OneToOneField(SolicitudAdopcion, on_delete=models.CASCADE, related_name='seguimiento')
    fecha_visita = models.DateField()
    observaciones = models.TextField(blank=True)
    estado_mascota = models.CharField(max_length=15, choices=ESTADO_MASCOTA_CHOICES, default='bueno')
    recomendaciones = models.TextField(blank=True)
    id_admin_seguimiento = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='seguimientos_realizados')
    fecha_registro = models.DateTimeField(default=timezone.now)

# Modelo de Favoritos
class Favorito(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='favoritos')
    mascota = models.ForeignKey(Mascota, on_delete=models.CASCADE, related_name='seguidores')
    fecha_agregado = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('usuario', 'mascota')

# Modelo de Donaciones
class Donacion(models.Model):
    TIPO_DONACION_CHOICES = [
        ('monetaria', 'Monetaria'),
        ('insumos', 'Insumos'),
    ]
    MEDIO_PAGO_CHOICES = [
        ('pse', 'PSE'),
        ('tarjeta_credito', 'Tarjeta de Crédito'),
        ('cheque', 'Cheque'),
    ]
    CATEGORIA_INSUMO_CHOICES = [
        ('alimentos', 'Alimentos'),
        ('medicamentos', 'Medicamentos'),
        ('juguetes', 'Juguetes'),
        ('arena', 'Arena para gatos'),
        ('otros', 'Otros'),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='donaciones')
    nombre_donante = models.CharField(max_length=100)
    apellido_donante = models.CharField(max_length=100)
    email_donante = models.EmailField()
    telefono_donante = models.CharField(max_length=20, blank=True)
    
    tipo_donacion = models.CharField(max_length=20, choices=TIPO_DONACION_CHOICES)
    
    # Campos para donación MONETARIA
    monto = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[
            MinValueValidator(0.01, message="El monto debe ser mayor a 0.")
        ]
    )
    medio_pago = models.CharField(max_length=20, choices=MEDIO_PAGO_CHOICES, null=True, blank=True)
    
    # Campos para donación de INSUMOS
    categoria_insumo = models.CharField(max_length=20, choices=CATEGORIA_INSUMO_CHOICES, null=True, blank=True)
    descripcion_insumo = models.TextField(blank=True, help_text="Describe los insumos que vas a donar.")
    
    fecha_donacion = models.DateTimeField(auto_now_add=True)
    comprobante_url = models.CharField(max_length=500, blank=True) # para almacenar la ruta al PDF

    def __str__(self):
        return f"Donación de {self.nombre_donante} {self.apellido_donante} - {self.get_tipo_donacion_display()}"

# Modelo de Mensajes de Contacto
class Mensaje(models.Model):
    ESTADO_CHOICES = (
        ('no_leido', 'No Leído'),
        ('leido', 'Leído'),
        ('respondido', 'Respondido'),
    )
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True)
    asunto = models.CharField(max_length=200)
    mensaje = models.TextField()
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='no_leido')
    fecha_envio = models.DateTimeField(default=timezone.now)
    id_admin_respuesta = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='mensajes_respondidos')
    fecha_respuesta = models.DateTimeField(null=True, blank=True)

# Modelo de Configuración del Sitio
class ConfiguracionSitio(models.Model):
    clave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    descripcion = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return self.clave

class PasswordResetCode(models.Model):
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE)
    codigo = models.CharField(max_length=6)
    creado = models.DateTimeField(auto_now_add=True)
    expiracion = models.DateTimeField()
    usado = models.BooleanField(default=False)

    def es_valido(self):
        return not self.usado and timezone.now() < self.expiracion

    def __str__(self):
        return f"Código para {self.usuario.email} ({self.codigo})"

class HistorialMascota(models.Model):
    mascota = models.ForeignKey('Mascota', on_delete=models.CASCADE)
    estado_anterior = models.CharField(max_length=30)
    estado_nuevo = models.CharField(max_length=30)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    observacion = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey('Usuario', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.mascota.nombre}: {self.estado_anterior} → {self.estado_nuevo} ({self.fecha_cambio:%Y-%m-%d %H:%M})"

class SeguimientoMascota(models.Model):
    mascota = models.ForeignKey('Mascota', on_delete=models.CASCADE)
    adoptante = models.ForeignKey('Usuario', on_delete=models.CASCADE)
    fecha_inicio = models.DateField(auto_now_add=True)
    proxima_cita = models.DateField()
    numero_cita = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(3)])  # 1, 2 o 3
    completada = models.BooleanField(default=False)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Seguimiento {self.mascota.nombre} - Cita {self.numero_cita}"
