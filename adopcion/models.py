from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
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
    
    nombre = models.CharField(
        max_length=100, 
        blank=False, 
        null=False,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$',
                message="El nombre solo puede contener letras y espacios."
            )
        ]
    )
    apellido = models.CharField(
        max_length=100, 
        blank=False, 
        null=False,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$',
                message="El apellido solo puede contener letras y espacios."
            )
        ]
    )
    telefono = models.CharField(
        max_length=20, 
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^[\d\s\-\+\(\)]+$',
                message="El teléfono solo puede contener números, espacios, guiones, paréntesis y el símbolo +."
            )
        ]
    )
    direccion = models.TextField(blank=True)
    ciudad = models.CharField(
        max_length=100, 
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$',
                message="La ciudad solo puede contener letras y espacios."
            )
        ]
    )
    fecha_nacimiento = models.DateField(null=True, blank=True)
    ocupacion = models.CharField(
        max_length=100, 
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$',
                message="La ocupación solo puede contener letras y espacios."
            )
        ]
    )
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
    CATEGORIA_CHOICES = (
        ('cachorro', 'Cachorro'),
        ('joven', 'Joven'),
        ('adulto', 'Adulto'),
        ('senior', 'Senior'),
        ('especial', 'Necesidades Especiales'),
        ('urgente', 'Adopción Urgente'),
        ('rescatado', 'Recién Rescatado'),
        ('recuperacion', 'En Recuperación'),
        ('socializacion', 'En Socialización'),
    )

    nombre = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$',
                message="El nombre solo puede contener letras y espacios."
            )
        ]
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='adulto')
    raza = models.CharField(max_length=100, blank=True)
    
    # Cambio: Ahora usamos fecha de nacimiento en lugar de edad aproximada
    fecha_nacimiento = models.DateField(
        null=True, 
        blank=True,
        help_text="Fecha de nacimiento aproximada de la mascota"
    )
    edad_aproximada_meses = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Edad aproximada en meses (se calcula automáticamente si no se proporciona fecha de nacimiento)",
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
            MinValueValidator(0.1, message="El peso debe ser mayor a 0.1 kg."),
            MaxValueValidator(200.0, message="El peso no puede exceder 200 kg.")
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
        return f"{self.nombre} ({self.get_tipo_display()})"

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
        return dict(self.ESTADO_ADOPCION_CHOICES).get(self.estado_adopcion, self.estado_adopcion)
    
    def get_tipo_display(self):
        """Obtiene el tipo de mascota en formato legible"""
        return dict(self.TIPO_CHOICES).get(self.tipo, self.tipo)
    
    def get_sexo_display(self):
        """Obtiene el sexo en formato legible"""
        return dict(self.SEXO_CHOICES).get(self.sexo, self.sexo)
    
    def get_tamaño_display(self):
        """Obtiene el tamaño en formato legible"""
        return dict(self.TAMAÑO_CHOICES).get(self.tamaño, self.tamaño)
    
    def get_categoria_display(self):
        """Obtiene la categoría en formato legible"""
        return dict(self.CATEGORIA_CHOICES).get(self.categoria, self.categoria)
    
    @property
    def edad_actual_meses(self):
        """Calcula la edad actual en meses basada en la fecha de nacimiento o edad aproximada"""
        if self.fecha_nacimiento:
            from datetime import date
            hoy = date.today()
            edad = hoy.year - self.fecha_nacimiento.year
            if hoy.month < self.fecha_nacimiento.month or (hoy.month == self.fecha_nacimiento.month and hoy.day < self.fecha_nacimiento.day):
                edad -= 1
            return edad * 12 + (hoy.month - self.fecha_nacimiento.month)
        elif self.edad_aproximada_meses:
            return self.edad_aproximada_meses
        return 0

    @property
    def edad_actual_anios(self):
        """Calcula la edad actual en años"""
        return self.edad_actual_meses // 12

    @property
    def edad_actual_meses_restantes(self):
        """Calcula los meses restantes después de los años completos"""
        return self.edad_actual_meses % 12

    def get_edad_display(self):
        """Obtiene una representación legible de la edad"""
        anios = self.edad_actual_anios
        meses = self.edad_actual_meses_restantes
        
        if anios == 0:
            if meses == 1:
                return "1 mes"
            elif meses == 0:
                return "Menos de 1 mes"
            else:
                return f"{meses} meses"
        elif anios == 1:
            if meses == 0:
                return "1 año"
            elif meses == 1:
                return "1 año y 1 mes"
            else:
                return f"1 año y {meses} meses"
        else:
            if meses == 0:
                return f"{anios} años"
            elif meses == 1:
                return f"{anios} años y 1 mes"
            else:
                return f"{anios} años y {meses} meses"

    @classmethod
    def contar_peludos_en_fundacion(cls):
        """Cuenta cuántos peludos hay actualmente en la fundación"""
        return cls.objects.filter(estado_adopcion='disponible').count()
    
    @classmethod
    def contar_peludos_adoptados(cls):
        """Cuenta cuántos peludos han sido adoptados"""
        return cls.objects.filter(estado_adopcion='adoptado').count()
    
    @classmethod
    def obtener_estadisticas_peludos(cls):
        """Obtiene estadísticas completas de los peludos"""
        total = cls.objects.count()
        disponibles = cls.contar_peludos_en_fundacion()
        adoptados = cls.contar_peludos_adoptados()
        en_proceso = cls.objects.filter(estado_adopcion='en_proceso').count()
        no_disponibles = cls.objects.filter(estado_adopcion='no_disponible').count()
        
        return {
            'total': total,
            'disponibles': disponibles,
            'adoptados': adoptados,
            'en_proceso': en_proceso,
            'no_disponibles': no_disponibles,
        }
    
    def save(self, *args, **kwargs):
        """Sobrescribe el método save para asegurar que las imágenes se adapten correctamente"""
        # Si es una nueva mascota y no tiene fecha de ingreso, asignar la fecha actual
        if not self.pk and not self.fecha_ingreso:
            self.fecha_ingreso = timezone.now().date()
        
        # Si se proporciona fecha de nacimiento, calcular edad aproximada
        if self.fecha_nacimiento and not self.edad_aproximada_meses:
            self.edad_aproximada_meses = self.edad_actual_meses
        
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
        ('servicios', 'Servicios'),
        ('especie', 'En Especie'),
    ]
    MEDIO_PAGO_CHOICES = [
        ('pse', 'PSE'),
        ('tarjeta_credito', 'Tarjeta de Crédito'),
        ('tarjeta_debito', 'Tarjeta de Débito'),
        ('transferencia', 'Transferencia Bancaria'),
        ('efectivo', 'Efectivo'),
        ('cheque', 'Cheque'),
        ('otro', 'Otro'),
    ]
    FRECUENCIA_CHOICES = [
        ('unica', 'Donación Única'),
        ('mensual', 'Donación Mensual'),
        ('trimestral', 'Donación Trimestral'),
        ('semestral', 'Donación Semestral'),
        ('anual', 'Donación Anual'),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='donaciones')
    nombre_donante = models.CharField(max_length=100)
    apellido_donante = models.CharField(max_length=100)
    email_donante = models.EmailField()
    telefono_donante = models.CharField(max_length=20, blank=True)
    
    # Información adicional del donante
    tipo_identificacion = models.CharField(max_length=20, choices=[
        ('cc', 'Cédula de Ciudadanía'),
        ('ce', 'Cédula de Extranjería'),
        ('pasaporte', 'Pasaporte'),
        ('nit', 'NIT'),
        ('otro', 'Otro'),
    ], default='cc')
    numero_identificacion = models.CharField(max_length=20, blank=True)
    direccion_donante = models.TextField(blank=True)
    ciudad_donante = models.CharField(max_length=100, blank=True)
    
    # Información de la donación
    tipo_donacion = models.CharField(max_length=20, choices=TIPO_DONACION_CHOICES)
    frecuencia = models.CharField(max_length=20, choices=FRECUENCIA_CHOICES, default='unica')
    fecha_donacion = models.DateTimeField(auto_now_add=True)
    
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
    comprobante_pago = models.FileField(upload_to='comprobantes/', null=True, blank=True)
    
    # Campos para donación de INSUMOS - Ahora usando categorías dinámicas
    categoria_insumo = models.ForeignKey('CategoriaDonacion', on_delete=models.SET_NULL, null=True, blank=True)
    descripcion_insumo = models.TextField(blank=True, help_text="Describe los insumos que vas a donar.")
    cantidad_insumo = models.PositiveIntegerField(null=True, blank=True, help_text="Cantidad de unidades")
    unidad_medida = models.CharField(max_length=20, blank=True, help_text="Ej: kg, litros, unidades")
    
    # Campos para donación de SERVICIOS
    tipo_servicio = models.CharField(max_length=100, blank=True, help_text="Tipo de servicio ofrecido")
    descripcion_servicio = models.TextField(blank=True, help_text="Descripción del servicio")
    horas_servicio = models.PositiveIntegerField(null=True, blank=True, help_text="Horas de servicio")
    fecha_servicio = models.DateField(null=True, blank=True, help_text="Fecha para realizar el servicio")
    
    # Campos para donación EN ESPECIE
    descripcion_especie = models.TextField(blank=True, help_text="Descripción de la donación en especie")
    valor_estimado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Información adicional
    motivo_donacion = models.TextField(blank=True, help_text="¿Por qué decides donar?")
    anonimo = models.BooleanField(default=False, help_text="¿Deseas que tu donación sea anónima?")
    recibir_informacion = models.BooleanField(default=True, help_text="¿Deseas recibir información sobre el uso de tu donación?")
    
    # Estado y seguimiento
    estado_donacion = models.CharField(max_length=20, choices=[
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('rechazada', 'Rechazada'),
        ('cancelada', 'Cancelada'),
    ], default='pendiente')
    
    comentarios_admin = models.TextField(blank=True, help_text="Comentarios internos del administrador")
    fecha_confirmacion = models.DateTimeField(null=True, blank=True)
    admin_confirmador = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='donaciones_confirmadas')

    def __str__(self):
        if self.anonimo:
            return f"Donación Anónima - {self.get_tipo_donacion_display()}"
        return f"Donación de {self.nombre_donante} {self.apellido_donante} - {self.get_tipo_donacion_display()}"
    
    def get_valor_total(self):
        """Obtiene el valor total de la donación"""
        if self.tipo_donacion == 'monetaria' and self.monto:
            return self.monto
        elif self.tipo_donacion == 'especie' and self.valor_estimado:
            return self.valor_estimado
        return 0
    
    def get_descripcion_completa(self):
        """Obtiene una descripción completa de la donación"""
        if self.tipo_donacion == 'monetaria':
            return f"${self.monto:,.0f} COP - {self.get_medio_pago_display()}"
        elif self.tipo_donacion == 'insumos':
            return f"{self.cantidad_insumo or 0} {self.unidad_medida or 'unidades'} - {self.categoria_insumo}"
        elif self.tipo_donacion == 'servicios':
            return f"{self.horas_servicio or 0} horas - {self.tipo_servicio}"
        elif self.tipo_donacion == 'especie':
            return f"En especie - ${self.valor_estimado:,.0f} COP estimado"
        return "Sin descripción"

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

class CitaPreAdopcion(models.Model):
    ESTADO_CHOICES = (
        ('programada', 'Programada'),
        ('confirmada', 'Confirmada'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
        ('reprogramada', 'Reprogramada'),
    )
    
    solicitud = models.OneToOneField('SolicitudAdopcion', on_delete=models.CASCADE, related_name='cita_pre_adopcion')
    fecha_cita = models.DateTimeField()
    duracion_minutos = models.PositiveIntegerField(default=30, help_text="Duración en minutos")
    lugar = models.CharField(max_length=200, default="Fundación Luna & Lía")
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='programada')
    observaciones_admin = models.TextField(blank=True, help_text="Observaciones internas del administrador")
    observaciones_usuario = models.TextField(blank=True, help_text="Observaciones del usuario")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cita para {self.solicitud.mascota.nombre} - {self.solicitud.usuario.username} - {self.fecha_cita.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def mascota(self):
        return self.solicitud.mascota
    
    @property
    def usuario(self):
        return self.solicitud.usuario

class CategoriaDonacion(models.Model):
    """Modelo para categorías de donaciones dinámicas que puede gestionar el administrador"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Categoría de Donación"
        verbose_name_plural = "Categorías de Donaciones"

class Notificacion(models.Model):
    """Modelo para notificaciones internas del sistema"""
    TIPO_CHOICES = (
        ('solicitud', 'Nueva Solicitud'),
        ('cita', 'Cita Programada'),
        ('estado', 'Cambio de Estado'),
        ('donacion', 'Nueva Donación'),
        ('seguimiento', 'Seguimiento'),
        ('general', 'General'),
    )
    
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones')
    tipo = models.CharField(max_length=50)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_lectura = models.DateTimeField(null=True, blank=True)
    
    # Campos opcionales para referenciar otros modelos
    solicitud = models.ForeignKey(SolicitudAdopcion, on_delete=models.CASCADE, null=True, blank=True)
    mascota = models.ForeignKey(Mascota, on_delete=models.CASCADE, null=True, blank=True)
    donacion = models.ForeignKey(Donacion, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"{self.tipo}: {self.titulo} - {self.usuario.username}"
    
    class Meta:
        ordering = ['-fecha_creacion']

class SeguimientoMascota(models.Model):
    """Modelo para seguimiento de mascotas"""
    mascota = models.ForeignKey(Mascota, on_delete=models.CASCADE, related_name='seguimientos')
    fecha_seguimiento = models.DateTimeField(default=timezone.now)
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    estado_salud = models.TextField(default="Bueno")
    observaciones = models.TextField(blank=True, default="")
    proxima_revision = models.DateField(null=True, blank=True)
    administrador = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Seguimiento de {self.mascota.nombre} - {self.fecha_seguimiento.strftime('%d/%m/%Y')}"
    
    class Meta:
        ordering = ['-fecha_seguimiento']
