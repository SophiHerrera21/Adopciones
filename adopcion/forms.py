from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from .models import SolicitudAdopcion, Donacion, Usuario, Mascota, FotoMascota, CategoriaDonacion, SeguimientoMascota
from django.utils import timezone
from datetime import date

class RegistroUsuarioForm(UserCreationForm):
    nombre = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}))
    apellido = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}))
    username = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de Usuario'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo Electrónico'}))
    telefono = forms.CharField(max_length=10, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono (10 dígitos)'}))
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}),
        help_text="Mínimo 5 caracteres, puede incluir letras, números y símbolos"
    )
    password2 = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmar Contraseña'})
    )

    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'username', 'email', 'telefono', 'password1', 'password2']

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if len(password) < 5:
            raise ValidationError('La contraseña debe tener al menos 5 caracteres.')
        return password

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '')
        if not telefono.isdigit() or len(telefono) != 10:
            raise ValidationError('El teléfono debe tener exactamente 10 dígitos numéricos.')
        return telefono

class BusquedaMascotasForm(forms.Form):
    """Formulario de búsqueda avanzada de mascotas"""
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, raza, personalidad...'
        })
    )
    tipo = forms.ChoiceField(
        choices=[('', 'Cualquier especie')] + list(Mascota.TIPO_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    categoria = forms.ChoiceField(
        choices=[('', 'Cualquier categoría')] + list(Mascota.CATEGORIA_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    sexo = forms.ChoiceField(
        choices=[('', 'Cualquier sexo')] + list(Mascota.SEXO_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    tamaño = forms.ChoiceField(
        choices=[('', 'Cualquier tamaño')] + list(Mascota.TAMAÑO_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    estado_adopcion = forms.ChoiceField(
        choices=[('', 'Cualquier estado')] + list(Mascota.ESTADO_ADOPCION_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    edad_min = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '204',
            'placeholder': 'Edad mínima (meses)'
        })
    )
    edad_max = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '204',
            'placeholder': 'Edad máxima (meses)'
        })
    )
    peso_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0.1',
            'max': '200.0',
            'step': '0.1',
            'placeholder': 'Peso mínimo (kg)'
        })
    )
    peso_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0.1',
            'max': '200.0',
            'step': '0.1',
            'placeholder': 'Peso máximo (kg)'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        edad_min = cleaned_data.get('edad_min')
        edad_max = cleaned_data.get('edad_max')
        peso_min = cleaned_data.get('peso_min')
        peso_max = cleaned_data.get('peso_max')

        if edad_min and edad_max and edad_min > edad_max:
            raise ValidationError('La edad mínima no puede ser mayor que la edad máxima.')

        if peso_min and peso_max and peso_min > peso_max:
            raise ValidationError('El peso mínimo no puede ser mayor que el peso máximo.')

        return cleaned_data

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username', 'email', 'nombre', 'apellido')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar mensajes de ayuda
        self.fields['username'].help_text = 'Requerido. 150 caracteres o menos. Solo letras, dígitos y @/./+/-/_'
        self.fields['password1'].help_text = 'Tu contraseña debe contener al menos 5 caracteres.'
        self.fields['password2'].help_text = 'Ingresa la misma contraseña que antes, para verificación.'
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise ValidationError('El nombre de usuario es obligatorio.')
        if len(username) < 5:
            raise ValidationError('El nombre de usuario debe tener al menos 5 caracteres.')
        if Usuario.objects.filter(username=username).exists():
            raise ValidationError('Este nombre de usuario ya está en uso.')
        return username
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if not password1:
            raise ValidationError('La contraseña es obligatoria.')
        if len(password1) < 5:
            raise ValidationError('La contraseña debe tener al menos 5 caracteres.')
        return password1
    
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if not nombre:
            raise ValidationError('El nombre es obligatorio.')
        if len(nombre.strip()) < 5:
            raise ValidationError('El nombre debe tener al menos 5 caracteres.')
        if not nombre.replace(' ', '').isalpha():
            raise ValidationError('El nombre solo debe contener letras y espacios.')
        return nombre.strip()
    
    def clean_apellido(self):
        apellido = self.cleaned_data.get('apellido')
        if not apellido:
            raise ValidationError('El apellido es obligatorio.')
        if len(apellido.strip()) < 5:
            raise ValidationError('El apellido debe tener al menos 5 caracteres.')
        if not apellido.replace(' ', '').isalpha():
            raise ValidationError('El apellido solo debe contener letras y espacios.')
        return apellido.strip()
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError('El correo electrónico es obligatorio.')
        if len(email) < 10:
            raise ValidationError('El correo electrónico debe tener al menos 10 caracteres.')
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        return email.lower().strip()

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'email', 'telefono', 'direccion', 'ciudad']
    
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if not nombre:
            raise ValidationError('El nombre es obligatorio.')
        if len(nombre.strip()) < 5:
            raise ValidationError('El nombre debe tener al menos 5 caracteres.')
        if not nombre.replace(' ', '').isalpha():
            raise ValidationError('El nombre solo debe contener letras y espacios.')
        return nombre.strip()
    
    def clean_apellido(self):
        apellido = self.cleaned_data.get('apellido')
        if not apellido:
            raise ValidationError('El apellido es obligatorio.')
        if len(apellido.strip()) < 5:
            raise ValidationError('El apellido debe tener al menos 5 caracteres.')
        if not apellido.replace(' ', '').isalpha():
            raise ValidationError('El apellido solo debe contener letras y espacios.')
        return apellido.strip()
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError('El correo electrónico es obligatorio.')
        if len(email) < 10:
            raise ValidationError('El correo electrónico debe tener al menos 10 caracteres.')
        return email.lower().strip()
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '')
        if not telefono.isdigit() or len(telefono) != 10:
            raise ValidationError('El teléfono debe tener exactamente 10 dígitos numéricos.')
        return telefono
    
    def clean_direccion(self):
        direccion = self.cleaned_data.get('direccion')
        if direccion and len(direccion.strip()) < 10:
            raise ValidationError('La dirección debe tener al menos 10 caracteres.')
        return direccion.strip() if direccion else direccion
    
    def clean_ciudad(self):
        ciudad = self.cleaned_data.get('ciudad')
        if ciudad and len(ciudad.strip()) < 3:
            raise ValidationError('La ciudad debe tener al menos 3 caracteres.')
        return ciudad.strip() if ciudad else ciudad

class SolicitudAdopcionForm(forms.ModelForm):
    class Meta:
        model = SolicitudAdopcion
        fields = [
            'vivienda', 'es_propia', 'tiene_patio', 'tamano_patio', 'adultos_en_casa',
            'ninos_en_casa', 'edades_ninos', 'tuvo_mascotas', 'experiencia_mascotas',
            'otras_mascotas', 'tiempo_diario', 'todos_deacuerdo', 'cuidador_principal',
            'plan_vacaciones', 'ingreso_aproximado', 'presupuesto_mensual_mascota',
            'tiene_veterinario', 'nombre_veterinario', 'motivo_adopcion',
            'manejo_comportamiento', 'compromiso_largo_plazo',
            'preferencias_mascota', 'comentario_extra'
        ]
        widgets = {
            'edades_ninos': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ej: 5 años, 8 años', 'class': 'form-control campo-condicional'}),
            'experiencia_mascotas': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe tu experiencia previa con mascotas...', 'class': 'form-control campo-condicional'}),
            'tiempo_diario': forms.TextInput(attrs={'placeholder': 'Ej: 2-3 horas diarias', 'class': 'form-control'}),
            'plan_vacaciones': forms.Textarea(attrs={'rows': 3, 'placeholder': '¿Qué harías con la mascota cuando viajes?', 'class': 'form-control'}),
            'ingreso_aproximado': forms.TextInput(attrs={'placeholder': 'Ej: $2,000,000 - $3,000,000', 'class': 'form-control'}),
            'presupuesto_mensual_mascota': forms.TextInput(attrs={'placeholder': 'Ej: $200,000 - $300,000', 'class': 'form-control'}),
            'motivo_adopcion': forms.Textarea(attrs={'rows': 3, 'placeholder': '¿Por qué quieres adoptar una mascota?', 'class': 'form-control'}),
            'manejo_comportamiento': forms.Textarea(attrs={'rows': 3, 'placeholder': '¿Cómo manejarías problemas de comportamiento?', 'class': 'form-control'}),
            'preferencias_mascota': forms.Textarea(attrs={'rows': 3, 'placeholder': '¿Tienes alguna preferencia específica?', 'class': 'form-control'}),
            'comentario_extra': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Comentarios adicionales que quieras compartir...', 'class': 'form-control'}),
            'vivienda': forms.Select(attrs={'class': 'form-control'}),
            'es_propia': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tiene_patio': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tamano_patio': forms.Select(attrs={'class': 'form-control campo-condicional'}),
            'adultos_en_casa': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'ninos_en_casa': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'tuvo_mascotas': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'otras_mascotas': forms.TextInput(attrs={'class': 'form-control campo-condicional'}),
            'todos_deacuerdo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cuidador_principal': forms.TextInput(attrs={'class': 'form-control'}),
            'tiene_veterinario': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'nombre_veterinario': forms.TextInput(attrs={'class': 'form-control campo-condicional'}),
            'compromiso_largo_plazo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar etiquetas
        self.fields['vivienda'].label = 'Tipo de Vivienda'
        self.fields['es_propia'].label = '¿La vivienda es propia?'
        self.fields['tiene_patio'].label = '¿Tiene patio o terraza?'
        self.fields['tamano_patio'].label = 'Tamaño del Patio'
        self.fields['adultos_en_casa'].label = '¿Cuántos adultos viven en la casa?'
        self.fields['ninos_en_casa'].label = '¿Cuántos niños viven en la casa?'
        self.fields['edades_ninos'].label = 'Edades de los niños'
        self.fields['tuvo_mascotas'].label = '¿Ha tenido mascotas antes?'
        self.fields['experiencia_mascotas'].label = 'Describa su experiencia con mascotas'
        self.fields['otras_mascotas'].label = '¿Qué otras mascotas tiene actualmente?'
        self.fields['tiempo_diario'].label = '¿Cuánto tiempo diario puede dedicarle a la mascota?'
        self.fields['todos_deacuerdo'].label = '¿Todos en casa están de acuerdo con la adopción?'
        self.fields['cuidador_principal'].label = '¿Quién será el cuidador principal?'
        self.fields['plan_vacaciones'].label = '¿Qué planes tiene para la mascota en vacaciones?'
        self.fields['ingreso_aproximado'].label = 'Ingreso mensual aproximado del hogar'
        self.fields['presupuesto_mensual_mascota'].label = 'Presupuesto mensual para la mascota'
        self.fields['tiene_veterinario'].label = '¿Tiene un veterinario de confianza?'
        self.fields['nombre_veterinario'].label = 'Nombre del Veterinario'
        self.fields['motivo_adopcion'].label = '¿Por qué desea adoptar?'
        self.fields['manejo_comportamiento'].label = '¿Cómo manejaría un problema de comportamiento?'
        self.fields['compromiso_largo_plazo'].label = '¿Se compromete a cuidarlo por toda su vida? (15 años o más)'
        self.fields['preferencias_mascota'].label = '¿Tiene alguna preferencia sobre la mascota?'
        self.fields['comentario_extra'].label = 'Comentarios adicionales'

    def clean(self):
        cleaned_data = super().clean()
        import datetime
        hoy = datetime.datetime.now()
        if hoy.weekday() == 6:  # 6 = Domingo
            raise forms.ValidationError('Las solicitudes de pre-adopción solo se pueden realizar de lunes a sábado.')
        ninos_en_casa = cleaned_data.get('ninos_en_casa')
        edades_ninos = cleaned_data.get('edades_ninos')
        adultos_en_casa = cleaned_data.get('adultos_en_casa')
        
        # Validar que no haya valores negativos
        if ninos_en_casa is not None and ninos_en_casa < 0:
            raise ValidationError('El número de niños no puede ser negativo.')
        
        if adultos_en_casa is not None and adultos_en_casa < 0:
            raise ValidationError('El número de adultos no puede ser negativo.')
        
        # Solo validar edades de niños si hay niños en casa
        if ninos_en_casa and ninos_en_casa > 0 and not edades_ninos:
            raise ValidationError('Si hay niños en casa, debe especificar sus edades.')
        
        return cleaned_data

class DonacionForm(forms.ModelForm):
    class Meta:
        model = Donacion
        fields = [
            'nombre_donante', 'apellido_donante', 'email_donante', 'telefono_donante',
            'tipo_identificacion', 'numero_identificacion', 'direccion_donante', 'ciudad_donante',
            'tipo_donacion', 'frecuencia', 'monto', 'medio_pago', 'comprobante_pago',
            'categoria_insumo', 'descripcion_insumo', 'cantidad_insumo', 'unidad_medida',
            'tipo_servicio', 'descripcion_servicio', 'horas_servicio', 'fecha_servicio',
            'descripcion_especie', 'valor_estimado', 'motivo_donacion', 'anonimo', 'recibir_informacion'
        ]
        widgets = {
            'nombre_donante': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu nombre',
                'pattern': '[a-zA-ZáéíóúÁÉÍÓÚñÑ\\s]+',
                'title': 'Solo letras y espacios'
            }),
            'apellido_donante': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu apellido',
                'pattern': '[a-zA-ZáéíóúÁÉÍÓÚñÑ\\s]+',
                'title': 'Solo letras y espacios'
            }),
            'email_donante': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'tu@email.com'
            }),
            'telefono_donante': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+57 300 123 4567',
                'pattern': '[\\d\\s\\-\\+\\(\\)]+',
                'title': 'Solo números, espacios, guiones, paréntesis y +'
            }),
            'tipo_identificacion': forms.Select(attrs={
                'class': 'form-control'
            }),
            'numero_identificacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de identificación'
            }),
            'direccion_donante': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Tu dirección completa'
            }),
            'ciudad_donante': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu ciudad'
            }),
            'tipo_donacion': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_tipo_donacion'
            }),
            'frecuencia': forms.Select(attrs={
                'class': 'form-control'
            }),
            'monto': forms.NumberInput(attrs={
                'class': 'form-control campo-monetario',
                'min': '1000',
                'step': '1000',
                'placeholder': 'Monto en pesos colombianos'
            }),
            'medio_pago': forms.Select(attrs={
                'class': 'form-control campo-monetario'
            }),
            'comprobante_pago': forms.FileInput(attrs={
                'class': 'form-control campo-monetario',
                'accept': 'image/*,.pdf'
            }),
            'categoria_insumo': forms.Select(attrs={
                'class': 'form-control campo-insumo'
            }),
            'descripcion_insumo': forms.Textarea(attrs={
                'class': 'form-control campo-insumo',
                'rows': 3,
                'placeholder': 'Describe los insumos que vas a donar...'
            }),
            'cantidad_insumo': forms.NumberInput(attrs={
                'class': 'form-control campo-insumo',
                'min': '1',
                'placeholder': 'Cantidad'
            }),
            'unidad_medida': forms.TextInput(attrs={
                'class': 'form-control campo-insumo',
                'placeholder': 'Ej: kg, litros, unidades'
            }),
            'tipo_servicio': forms.TextInput(attrs={
                'class': 'form-control campo-servicio',
                'placeholder': 'Ej: Voluntariado, Veterinaria, Limpieza'
            }),
            'descripcion_servicio': forms.Textarea(attrs={
                'class': 'form-control campo-servicio',
                'rows': 3,
                'placeholder': 'Describe el servicio que ofreces...'
            }),
            'horas_servicio': forms.NumberInput(attrs={
                'class': 'form-control campo-servicio',
                'min': '1',
                'placeholder': 'Horas de servicio'
            }),
            'fecha_servicio': forms.DateInput(attrs={
                'class': 'form-control campo-servicio',
                'type': 'date'
            }),
            'descripcion_especie': forms.Textarea(attrs={
                'class': 'form-control campo-especie',
                'rows': 3,
                'placeholder': 'Describe la donación en especie...'
            }),
            'valor_estimado': forms.NumberInput(attrs={
                'class': 'form-control campo-especie',
                'min': '1000',
                'step': '1000',
                'placeholder': 'Valor estimado en pesos'
            }),
            'motivo_donacion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '¿Por qué decides donar?'
            }),
            'anonimo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'recibir_informacion': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Si hay un usuario logueado, pre-llenar los datos
        if user and user.is_authenticated:
            self.fields['nombre_donante'].initial = user.nombre
            self.fields['apellido_donante'].initial = user.apellido
            self.fields['email_donante'].initial = user.email
            self.fields['telefono_donante'].initial = user.telefono
            self.fields['direccion_donante'].initial = user.direccion
            self.fields['ciudad_donante'].initial = user.ciudad
            
            # Hacer los campos de información personal readonly para usuarios logueados
            self.fields['nombre_donante'].widget.attrs['readonly'] = True
            self.fields['apellido_donante'].widget.attrs['readonly'] = True
            self.fields['email_donante'].widget.attrs['readonly'] = True
            self.fields['telefono_donante'].widget.attrs['readonly'] = True
        
        # Cargar categorías activas dinámicamente
        from .models import CategoriaDonacion
        categorias_activas = CategoriaDonacion.objects.filter(activa=True).order_by('nombre')
        self.fields['categoria_insumo'].queryset = categorias_activas
        
        # Personalizar etiquetas
        self.fields['nombre_donante'].label = 'Nombre'
        self.fields['apellido_donante'].label = 'Apellido'
        self.fields['email_donante'].label = 'Correo Electrónico'
        self.fields['telefono_donante'].label = 'Teléfono'
        self.fields['tipo_identificacion'].label = 'Tipo de Identificación'
        self.fields['numero_identificacion'].label = 'Número de Identificación'
        self.fields['direccion_donante'].label = 'Dirección'
        self.fields['ciudad_donante'].label = 'Ciudad'
        self.fields['tipo_donacion'].label = 'Tipo de Donación'
        self.fields['frecuencia'].label = 'Frecuencia'
        self.fields['monto'].label = 'Monto (COP)'
        self.fields['medio_pago'].label = 'Medio de Pago'
        self.fields['comprobante_pago'].label = 'Comprobante de Pago'
        self.fields['categoria_insumo'].label = 'Categoría de Insumo'
        self.fields['descripcion_insumo'].label = 'Descripción de Insumos'
        self.fields['cantidad_insumo'].label = 'Cantidad'
        self.fields['unidad_medida'].label = 'Unidad de Medida'
        self.fields['tipo_servicio'].label = 'Tipo de Servicio'
        self.fields['descripcion_servicio'].label = 'Descripción del Servicio'
        self.fields['horas_servicio'].label = 'Horas de Servicio'
        self.fields['fecha_servicio'].label = 'Fecha para Realizar el Servicio'
        self.fields['descripcion_especie'].label = 'Descripción de la Donación'
        self.fields['valor_estimado'].label = 'Valor Estimado (COP)'
        self.fields['motivo_donacion'].label = 'Motivo de la Donación'
        self.fields['anonimo'].label = '¿Deseas que tu donación sea anónima?'
        self.fields['recibir_informacion'].label = '¿Deseas recibir información sobre el uso de tu donación?'

    def clean_nombre_donante(self):
        nombre = self.cleaned_data.get('nombre_donante')
        if not nombre:
            raise ValidationError('El nombre es obligatorio.')
        if len(nombre.strip()) < 2:
            raise ValidationError('El nombre debe tener al menos 2 caracteres.')
        if not nombre.replace(' ', '').isalpha():
            raise ValidationError('El nombre solo debe contener letras y espacios.')
        return nombre.strip()

    def clean_apellido_donante(self):
        apellido = self.cleaned_data.get('apellido_donante')
        if not apellido:
            raise ValidationError('El apellido es obligatorio.')
        if len(apellido.strip()) < 2:
            raise ValidationError('El apellido debe tener al menos 2 caracteres.')
        if not apellido.replace(' ', '').isalpha():
            raise ValidationError('El apellido solo debe contener letras y espacios.')
        return apellido.strip()

    def clean_email_donante(self):
        email = self.cleaned_data.get('email_donante')
        if not email:
            raise ValidationError('El correo electrónico es obligatorio.')
        if len(email) < 10:
            raise ValidationError('El correo electrónico debe tener al menos 10 caracteres.')
        return email.lower().strip()

    def clean_telefono_donante(self):
        telefono = self.cleaned_data.get('telefono_donante', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '')
        if not telefono.isdigit() or len(telefono) != 10:
            raise ValidationError('El teléfono debe tener exactamente 10 dígitos numéricos.')
        return telefono

    def clean(self):
        cleaned_data = super().clean()
        tipo_donacion = cleaned_data.get('tipo_donacion')
        monto = cleaned_data.get('monto')
        medio_pago = cleaned_data.get('medio_pago')
        categoria_insumo = cleaned_data.get('categoria_insumo')
        descripcion_insumo = cleaned_data.get('descripcion_insumo')
        cantidad_insumo = cleaned_data.get('cantidad_insumo')
        tipo_servicio = cleaned_data.get('tipo_servicio')
        descripcion_servicio = cleaned_data.get('descripcion_servicio')
        horas_servicio = cleaned_data.get('horas_servicio')
        descripcion_especie = cleaned_data.get('descripcion_especie')
        valor_estimado = cleaned_data.get('valor_estimado')

        if tipo_donacion == 'monetaria':
            if not monto:
                raise ValidationError('Para donaciones monetarias, el monto es obligatorio.')
            if not medio_pago:
                raise ValidationError('Para donaciones monetarias, el medio de pago es obligatorio.')
        elif tipo_donacion == 'insumos':
            if not categoria_insumo:
                raise ValidationError('Para donaciones de insumos, la categoría es obligatoria.')
            if not descripcion_insumo:
                raise ValidationError('Para donaciones de insumos, la descripción es obligatoria.')
            if not cantidad_insumo:
                raise ValidationError('Para donaciones de insumos, la cantidad es obligatoria.')
        elif tipo_donacion == 'servicios':
            if not tipo_servicio:
                raise ValidationError('Para donaciones de servicios, el tipo de servicio es obligatorio.')
            if not descripcion_servicio:
                raise ValidationError('Para donaciones de servicios, la descripción es obligatoria.')
            if not horas_servicio:
                raise ValidationError('Para donaciones de servicios, las horas son obligatorias.')
        elif tipo_donacion == 'especie':
            if not descripcion_especie:
                raise ValidationError('Para donaciones en especie, la descripción es obligatoria.')

        return cleaned_data

    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        if monto is not None:
            if monto < 1000:
                raise ValidationError('El monto mínimo es de $1,000 pesos colombianos.')
            if monto > 10000000:
                raise ValidationError('El monto máximo es de $10,000,000 pesos colombianos.')
        return monto

    def clean_valor_estimado(self):
        valor = self.cleaned_data.get('valor_estimado')
        if valor is not None:
            if valor < 1000:
                raise ValidationError('El valor estimado mínimo es de $1,000 pesos colombianos.')
            if valor > 10000000:
                raise ValidationError('El valor estimado máximo es de $10,000,000 pesos colombianos.')
        return valor

class MascotaAdminForm(forms.ModelForm):
    """Formulario personalizado para que el administrador añada mascotas con imágenes adaptadas"""
    class Meta:
        model = Mascota
        fields = [
            'nombre', 'tipo', 'raza', 'edad_aproximada_meses', 'sexo', 'tamaño', 
            'peso', 'color', 'descripcion', 'personalidad', 'necesidades_especiales',
            'estado_salud', 'vacunas_completas', 'esterilizado', 'microchip',
            'estado_adopcion', 'fecha_ingreso', 'imagen_principal'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'raza': forms.TextInput(attrs={'class': 'form-control'}),
            'edad_aproximada_meses': forms.NumberInput(attrs={'min': '0'}),
            'sexo': forms.Select(attrs={'class': 'form-control'}),
            'tamaño': forms.Select(attrs={'class': 'form-control'}),
            'peso': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'personalidad': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'necesidades_especiales': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'estado_salud': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'vacunas_completas': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'esterilizado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'microchip': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'estado_adopcion': forms.Select(attrs={'class': 'form-control'}),
            'fecha_ingreso': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'imagen_principal': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar etiquetas
        self.fields['edad_aproximada_meses'].label = 'Edad Aproximada (meses)'
        self.fields['estado_salud'].label = 'Estado de Salud'
        self.fields['vacunas_completas'].label = 'Vacunas Completas'
        self.fields['esterilizado'].label = 'Esterilizado'
        self.fields['microchip'].label = 'Microchip'
        self.fields['estado_adopcion'].label = 'Estado de Adopción'
        self.fields['fecha_ingreso'].label = 'Fecha de Ingreso'
        self.fields['imagen_principal'].label = 'Imagen Principal'

    def clean_edad_aproximada_meses(self):
        edad = self.cleaned_data.get('edad_aproximada_meses')
        if edad is not None:
            if edad < 0:
                raise ValidationError('La edad no puede ser negativa.')
            if edad > 204:
                raise ValidationError('La edad máxima es de 17 años (204 meses).')
        return edad

    def clean_peso(self):
        peso = self.cleaned_data.get('peso')
        if peso is not None:
            if peso <= 0:
                raise ValidationError('El peso debe ser mayor a 0.')
            if peso > 200:
                raise ValidationError('El peso no puede exceder 200 kg.')
        return peso

    def clean_fecha_ingreso(self):
        fecha = self.cleaned_data.get('fecha_ingreso')
        if fecha and fecha > timezone.now().date():
            raise ValidationError('La fecha de ingreso no puede ser futura.')
        return fecha

    def clean_imagen_principal(self):
        imagen = self.cleaned_data.get('imagen_principal')
        if imagen:
            # Validar tamaño del archivo (máximo 5MB)
            if imagen.size > 5 * 1024 * 1024:
                raise ValidationError('La imagen no puede ser mayor a 5MB.')
        return imagen

class ReporteMensualForm(forms.Form):
    MESES = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]
    
    # Pre-seleccionar mes y año actual
    current_year = timezone.now().year
    current_month = timezone.now().month

    mes = forms.ChoiceField(
        choices=MESES, 
        initial=current_month,
        label="Mes"
    )
    año = forms.IntegerField(
        initial=current_year,
        label="Año",
        min_value=2020, # Asumiendo que la fundación no es más vieja que esto
        max_value=current_year
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['año'].widget.attrs.update({
            'placeholder': 'Ej: 2024',
            'class': 'form-control'
        })
        self.fields['mes'].widget.attrs.update({
            'class': 'form-select'
        })

class PasswordResetEmailForm(forms.Form):
    email = forms.EmailField(label="Correo electrónico", widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Ingresa tu correo registrado',
        'autocomplete': 'off',
    }))

class PasswordResetCodeForm(forms.Form):
    codigo = forms.CharField(label="Código de recuperación", max_length=6, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Código recibido por correo',
        'autocomplete': 'off',
    }))

class PasswordResetNewPasswordForm(forms.Form):
    nueva_contraseña = forms.CharField(label="Nueva contraseña", widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Nueva contraseña',
        'autocomplete': 'off',
    }))
    confirmar_contraseña = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirma la nueva contraseña',
        'autocomplete': 'off',
    }))

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('nueva_contraseña')
        p2 = cleaned_data.get('confirmar_contraseña')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        if p1 and len(p1) < 5:
            raise forms.ValidationError('La contraseña debe tener al menos 5 caracteres.')
        return cleaned_data 

class BusquedaDonantesForm(forms.Form):
    """Formulario para búsqueda múltiple de donantes"""
    nombre = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Nombre del donante'
    }))
    apellido = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Apellido del donante'
    }))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Correo electrónico'
    }))
    tipo_donacion = forms.ChoiceField(
        choices=[('', 'Todos los tipos')] + Donacion.TIPO_DONACION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    categoria = forms.ModelChoiceField(
        queryset=CategoriaDonacion.objects.filter(activa=True),
        required=False,
        empty_label="Todas las categorías",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    fecha_desde = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'class': 'form-control',
        'type': 'date'
    }))
    fecha_hasta = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'class': 'form-control',
        'type': 'date'
    }))

class CategoriaDonacionForm(forms.ModelForm):
    """Formulario para gestionar categorías de donaciones"""
    class Meta:
        model = CategoriaDonacion
        fields = ['nombre', 'descripcion', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class SeguimientoMascotaForm(forms.ModelForm):
    """Formulario para seguimiento de mascotas"""
    class Meta:
        model = SeguimientoMascota
        fields = ['peso', 'estado_salud', 'observaciones', 'proxima_revision']
        widgets = {
            'peso': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estado_salud': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'proxima_revision': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class MascotaFormMejorado(forms.ModelForm):
    """Formulario mejorado para mascotas dividido en dos partes"""
    
    # Opciones predefinidas para mejor UX
    RAZAS_PERROS = [
        ('', 'Selecciona una raza'),
        ('labrador', 'Labrador Retriever'),
        ('golden', 'Golden Retriever'),
        ('pastor_aleman', 'Pastor Alemán'),
        ('bulldog', 'Bulldog'),
        ('beagle', 'Beagle'),
        ('poodle', 'Poodle'),
        ('rottweiler', 'Rottweiler'),
        ('doberman', 'Doberman'),
        ('boxer', 'Boxer'),
        ('chihuahua', 'Chihuahua'),
        ('pug', 'Pug'),
        ('husky', 'Husky Siberiano'),
        ('criollo', 'Criollo'),
        ('otro', 'Otra raza'),
    ]
    
    RAZAS_GATOS = [
        ('', 'Selecciona una raza'),
        ('siames', 'Siamés'),
        ('persa', 'Persa'),
        ('main_coon', 'Maine Coon'),
        ('bengala', 'Bengala'),
        ('ragdoll', 'Ragdoll'),
        ('british_shorthair', 'British Shorthair'),
        ('sphynx', 'Sphynx'),
        ('abyssinian', 'Abisinio'),
        ('russian_blue', 'Azul Ruso'),
        ('criollo', 'Criollo'),
        ('otro', 'Otra raza'),
    ]
    
    # Campos del formulario con mejor UX
    nombre = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de la mascota',
            'pattern': '[a-zA-ZáéíóúÁÉÍÓÚñÑ\\s]+',
            'title': 'Solo letras y espacios'
        }),
        validators=[
            RegexValidator(
                regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$',
                message="El nombre solo puede contener letras y espacios."
            )
        ]
    )
    
    tipo = forms.ChoiceField(
        choices=Mascota.TIPO_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_tipo'
        })
    )
    
    categoria = forms.ChoiceField(
        choices=Mascota.CATEGORIA_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    raza = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_raza'
        })
    )
    
    # Cambio: Usar fecha de nacimiento en lugar de edad aproximada
    fecha_nacimiento = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'Fecha de nacimiento aproximada'
        }),
        help_text="Si no conoces la fecha exacta, puedes usar una aproximada"
    )
    
    edad_aproximada_meses = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '204',
            'placeholder': 'Edad en meses (si no tienes fecha de nacimiento)'
        }),
        help_text="Solo si no tienes fecha de nacimiento"
    )
    
    sexo = forms.ChoiceField(
        choices=Mascota.SEXO_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    tamaño = forms.ChoiceField(
        choices=Mascota.TAMAÑO_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    peso = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0.1',
            'max': '200.0',
            'step': '0.1',
            'placeholder': 'Peso en kg (opcional)'
        }),
        validators=[
            MinValueValidator(0.1, message="El peso debe ser mayor a 0.1 kg."),
            MaxValueValidator(200.0, message="El peso no puede exceder 200 kg.")
        ]
    )
    
    color = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Color de la mascota'
        })
    )
    
    descripcion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe las características físicas de la mascota...'
        })
    )
    
    personalidad = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe el temperamento y personalidad...'
        })
    )
    
    necesidades_especiales = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe necesidades especiales si las hay...'
        })
    )
    
    estado_salud = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe el estado de salud actual...'
        })
    )
    
    imagen_principal = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )

    class Meta:
        model = Mascota
        fields = [
            'nombre', 'tipo', 'categoria', 'raza', 'fecha_nacimiento', 'edad_aproximada_meses', 'sexo', 
            'tamaño', 'peso', 'color', 'descripcion', 'personalidad', 
            'necesidades_especiales', 'estado_salud', 'vacunas_completas', 
            'esterilizado', 'microchip', 'estado_adopcion', 'imagen_principal'
        ]
        widgets = {
            'vacunas_completas': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'esterilizado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'microchip': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'estado_adopcion': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configurar razas según el tipo seleccionado
        if self.instance.pk:
            if self.instance.tipo == 'perro':
                self.fields['raza'].choices = self.RAZAS_PERROS
            elif self.instance.tipo == 'gato':
                self.fields['raza'].choices = self.RAZAS_GATOS
        else:
            self.fields['raza'].choices = [('', 'Primero selecciona el tipo de mascota')]

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        fecha_nacimiento = cleaned_data.get('fecha_nacimiento')
        edad_aproximada_meses = cleaned_data.get('edad_aproximada_meses')
        
        # Validar que al menos uno de los dos campos de edad esté presente
        if not fecha_nacimiento and not edad_aproximada_meses:
            raise ValidationError('Debes proporcionar una fecha de nacimiento o una edad aproximada.')
        
        # Si se proporciona fecha de nacimiento, calcular edad aproximada automáticamente
        if fecha_nacimiento:
            from datetime import date
            hoy = date.today()
            edad = hoy.year - fecha_nacimiento.year
            if hoy.month < fecha_nacimiento.month or (hoy.month == fecha_nacimiento.month and hoy.day < fecha_nacimiento.day):
                edad -= 1
            edad_meses = edad * 12 + (hoy.month - fecha_nacimiento.month)
            cleaned_data['edad_aproximada_meses'] = edad_meses
        
        # Actualizar opciones de raza según el tipo
        if tipo == 'perro':
            self.fields['raza'].choices = self.RAZAS_PERROS
        elif tipo == 'gato':
            self.fields['raza'].choices = self.RAZAS_GATOS
        
        return cleaned_data 

class DonacionFormMejorado(forms.ModelForm):
    """Formulario mejorado para donaciones que usa datos del usuario registrado"""
    
    class Meta:
        model = Donacion
        fields = [
            'tipo_donacion', 'frecuencia', 'monto', 'medio_pago', 'comprobante_pago',
            'categoria_insumo', 'descripcion_insumo', 'cantidad_insumo', 'unidad_medida',
            'tipo_servicio', 'descripcion_servicio', 'horas_servicio', 'fecha_servicio',
            'descripcion_especie', 'valor_estimado', 'motivo_donacion', 'anonimo', 'recibir_informacion'
        ]
        widgets = {
            'tipo_donacion': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_tipo_donacion'
            }),
            'frecuencia': forms.Select(attrs={
                'class': 'form-control'
            }),
            'monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01',
                'placeholder': 'Monto de la donación'
            }),
            'medio_pago': forms.Select(attrs={
                'class': 'form-control'
            }),
            'comprobante_pago': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,.pdf'
            }),
            'categoria_insumo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'descripcion_insumo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe los insumos que vas a donar...'
            }),
            'cantidad_insumo': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Cantidad'
            }),
            'unidad_medida': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: kg, litros, unidades'
            }),
            'tipo_servicio': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tipo de servicio ofrecido'
            }),
            'descripcion_servicio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del servicio...'
            }),
            'horas_servicio': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Horas de servicio'
            }),
            'fecha_servicio': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'descripcion_especie': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la donación en especie...'
            }),
            'valor_estimado': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01',
                'placeholder': 'Valor estimado'
            }),
            'motivo_donacion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '¿Por qué decides donar?'
            }),
            'anonimo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'recibir_informacion': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.usuario = kwargs.pop('usuario', None)
        super().__init__(*args, **kwargs)
        
        # Hacer algunos campos opcionales según el tipo de donación
        self.fields['monto'].required = False
        self.fields['medio_pago'].required = False
        self.fields['categoria_insumo'].required = False
        self.fields['descripcion_insumo'].required = False
        self.fields['cantidad_insumo'].required = False
        self.fields['unidad_medida'].required = False
        self.fields['tipo_servicio'].required = False
        self.fields['descripcion_servicio'].required = False
        self.fields['horas_servicio'].required = False
        self.fields['fecha_servicio'].required = False
        self.fields['descripcion_especie'].required = False
        self.fields['valor_estimado'].required = False

    def clean(self):
        cleaned_data = super().clean()
        tipo_donacion = cleaned_data.get('tipo_donacion')
        
        if tipo_donacion == 'monetaria':
            if not cleaned_data.get('monto'):
                raise ValidationError('El monto es obligatorio para donaciones monetarias.')
            if not cleaned_data.get('medio_pago'):
                raise ValidationError('El medio de pago es obligatorio para donaciones monetarias.')
        
        elif tipo_donacion == 'insumos':
            if not cleaned_data.get('categoria_insumo'):
                raise ValidationError('La categoría de insumo es obligatoria.')
            if not cleaned_data.get('descripcion_insumo'):
                raise ValidationError('La descripción del insumo es obligatoria.')
            if not cleaned_data.get('cantidad_insumo'):
                raise ValidationError('La cantidad es obligatoria.')
        
        elif tipo_donacion == 'servicios':
            if not cleaned_data.get('tipo_servicio'):
                raise ValidationError('El tipo de servicio es obligatorio.')
            if not cleaned_data.get('descripcion_servicio'):
                raise ValidationError('La descripción del servicio es obligatoria.')
        
        elif tipo_donacion == 'especie':
            if not cleaned_data.get('descripcion_especie'):
                raise ValidationError('La descripción de la donación en especie es obligatoria.')
        
        return cleaned_data

    def save(self, commit=True):
        donacion = super().save(commit=False)
        if self.usuario:
            donacion.usuario = self.usuario
            donacion.nombre_donante = self.usuario.nombre
            donacion.apellido_donante = self.usuario.apellido
            donacion.email_donante = self.usuario.email
            donacion.telefono_donante = self.usuario.telefono
            donacion.direccion_donante = self.usuario.direccion
            donacion.ciudad_donante = self.usuario.ciudad
        if commit:
            donacion.save()
        return donacion 

class BusquedaDonacionesForm(forms.Form):
    """Formulario para búsqueda múltiple de donaciones"""
    nombre = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Nombre del donante'
    }))
    apellido = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Apellido del donante'
    }))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Correo electrónico'
    }))
    tipo_donacion = forms.ChoiceField(
        choices=[('', 'Todos los tipos')] + Donacion.TIPO_DONACION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    categoria = forms.ModelChoiceField(
        queryset=CategoriaDonacion.objects.filter(activa=True),
        required=False,
        empty_label="Todas las categorías",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    frecuencia = forms.ChoiceField(
        choices=[('', 'Todas las frecuencias')] + Donacion.FRECUENCIA_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    estado_donacion = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + [
            ('pendiente', 'Pendiente'),
            ('confirmada', 'Confirmada'),
            ('rechazada', 'Rechazada'),
            ('cancelada', 'Cancelada'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    fecha_desde = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'class': 'form-control',
        'type': 'date'
    }))
    fecha_hasta = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'class': 'form-control',
        'type': 'date'
    }))
    monto_min = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'min': '0.01',
        'step': '0.01',
        'placeholder': 'Monto mínimo'
    }))
    monto_max = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'min': '0.01',
        'step': '0.01',
        'placeholder': 'Monto máximo'
    }))
    anonimo = forms.ChoiceField(
        choices=[('', 'Todos'), ('True', 'Anónimas'), ('False', 'No anónimas')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        fecha_desde = cleaned_data.get('fecha_desde')
        fecha_hasta = cleaned_data.get('fecha_hasta')
        monto_min = cleaned_data.get('monto_min')
        monto_max = cleaned_data.get('monto_max')

        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise ValidationError('La fecha desde no puede ser mayor que la fecha hasta.')

        if monto_min and monto_max and monto_min > monto_max:
            raise ValidationError('El monto mínimo no puede ser mayor que el monto máximo.')

        return cleaned_data 