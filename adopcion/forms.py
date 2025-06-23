from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import SolicitudAdopcion, Donacion, Usuario, Mascota, FotoMascota
from django.utils import timezone
from datetime import date

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
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            # Limpiar el teléfono de caracteres especiales
            telefono_limpio = telefono.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
            if not telefono_limpio.isdigit():
                raise ValidationError('El teléfono debe contener solo números.')
            if len(telefono_limpio) < 7:
                raise ValidationError('El teléfono debe tener al menos 7 dígitos.')
            if len(telefono_limpio) > 15:
                raise ValidationError('El teléfono no puede tener más de 15 dígitos.')
        return telefono.strip() if telefono else telefono
    
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
            'manejo_comportamiento', 'compromiso_largo_plazo', 'acepta_visitas_seguimiento',
            'preferencias_mascota', 'comentario_extra'
        ]
        widgets = {
            'edades_ninos': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ej: 5 años, 8 años'}),
            'experiencia_mascotas': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe tu experiencia previa con mascotas...'}),
            'tiempo_diario': forms.TextInput(attrs={'placeholder': 'Ej: 2-3 horas diarias'}),
            'plan_vacaciones': forms.Textarea(attrs={'rows': 3, 'placeholder': '¿Qué harías con la mascota cuando viajes?'}),
            'ingreso_aproximado': forms.TextInput(attrs={'placeholder': 'Ej: $2,000,000 - $3,000,000'}),
            'presupuesto_mensual_mascota': forms.TextInput(attrs={'placeholder': 'Ej: $200,000 - $300,000'}),
            'motivo_adopcion': forms.Textarea(attrs={'rows': 3, 'placeholder': '¿Por qué quieres adoptar una mascota?'}),
            'manejo_comportamiento': forms.Textarea(attrs={'rows': 3, 'placeholder': '¿Cómo manejarías problemas de comportamiento?'}),
            'preferencias_mascota': forms.Textarea(attrs={'rows': 3, 'placeholder': '¿Tienes alguna preferencia específica?'}),
            'comentario_extra': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Comentarios adicionales que quieras compartir...'}),
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
        self.fields['acepta_visitas_seguimiento'].label = '¿Acepta visitas de seguimiento post-adopción?'
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
        
        if ninos_en_casa > 0 and not edades_ninos:
            raise ValidationError('Si hay niños en casa, debe especificar sus edades.')
        
        return cleaned_data

class DonacionForm(forms.ModelForm):
    class Meta:
        model = Donacion
        fields = [
            'nombre_donante', 'apellido_donante', 'email_donante', 'telefono_donante',
            'tipo_donacion', 'monto', 'medio_pago', 'categoria_insumo', 'descripcion_insumo'
        ]
        widgets = {
            'descripcion_insumo': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe los insumos que vas a donar...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar etiquetas
        self.fields['nombre_donante'].label = 'Nombre'
        self.fields['apellido_donante'].label = 'Apellido'
        self.fields['email_donante'].label = 'Correo Electrónico'
        self.fields['telefono_donante'].label = 'Teléfono'
        self.fields['tipo_donacion'].label = 'Tipo de Donación'
        self.fields['monto'].label = 'Monto a Donar'
        self.fields['medio_pago'].label = 'Medio de Pago'
        self.fields['categoria_insumo'].label = 'Categoría de Insumo'
        self.fields['descripcion_insumo'].label = 'Descripción de los Insumos'

    def clean_nombre_donante(self):
        nombre = self.cleaned_data.get('nombre_donante')
        if not nombre:
            raise ValidationError("El nombre es obligatorio.")
        if len(nombre.strip()) < 3:
            raise ValidationError("El nombre debe tener al menos 3 caracteres.")
        if not nombre.replace(' ', '').isalpha():
            raise ValidationError("El nombre solo debe contener letras y espacios.")
        return nombre.strip()

    def clean_email_donante(self):
        email = self.cleaned_data.get('email_donante')
        if not email:
            raise ValidationError("El correo electrónico es obligatorio.")
        # Se puede usar un validador de email de Django para más robustez, pero esto es un buen comienzo.
        if '@' not in email or '.' not in email.split('@')[-1]:
            raise ValidationError("Por favor, introduce una dirección de correo electrónico válida.")
        return email.lower().strip()

    def clean_telefono_donante(self):
        telefono = self.cleaned_data.get('telefono_donante')
        if telefono:
            telefono_limpio = ''.join(filter(str.isdigit, telefono))
            if not telefono_limpio:
                 raise ValidationError("El teléfono debe contener números.")
            if len(telefono_limpio) < 7 or len(telefono_limpio) > 15:
                raise ValidationError("El número de teléfono debe tener entre 7 y 15 dígitos.")
        return telefono

    def clean(self):
        cleaned_data = super().clean()
        tipo_donacion = cleaned_data.get('tipo_donacion')
        monto = cleaned_data.get('monto')
        medio_pago = cleaned_data.get('medio_pago')
        categoria_insumo = cleaned_data.get('categoria_insumo')
        descripcion_insumo = cleaned_data.get('descripcion_insumo')

        if tipo_donacion == 'monetaria':
            if not monto or monto <= 0:
                raise ValidationError('Para donaciones monetarias, debe especificar un monto válido mayor a 0.')
            if not medio_pago:
                raise ValidationError('Para donaciones monetarias, debe seleccionar un medio de pago.')
        elif tipo_donacion == 'insumos':
            if not categoria_insumo:
                raise ValidationError('Para donaciones de insumos, debe seleccionar una categoría.')
            if not descripcion_insumo:
                raise ValidationError('Para donaciones de insumos, debe describir los insumos que va a donar.')

        return cleaned_data

    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        if monto is not None:
            if monto <= 0:
                raise ValidationError('El monto debe ser mayor a 0.')
            if monto > 1000000000:  # 1 billón como límite máximo
                raise ValidationError('El monto no puede exceder $1,000,000,000.')
        return monto

class MascotaAdminForm(forms.ModelForm):
    """Formulario personalizado para que el administrador añada mascotas con imágenes adaptadas"""
    
    class Meta:
        model = Mascota
        fields = [
            'nombre', 'tipo', 'raza', 'edad_aproximada', 'sexo', 'tamaño', 
            'peso', 'color', 'descripcion', 'personalidad', 'necesidades_especiales',
            'estado_salud', 'vacunas_completas', 'esterilizado', 'microchip',
            'estado_adopcion', 'fecha_ingreso', 'imagen_principal'
        ]
        widgets = {
            'fecha_ingreso': forms.DateInput(attrs={'type': 'date'}),
            'descripcion': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe la personalidad y características de la mascota...'}),
            'personalidad': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe el temperamento y comportamiento...'}),
            'necesidades_especiales': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe si tiene necesidades especiales de cuidado...'}),
            'estado_salud': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe el estado de salud actual...'}),
            'imagen_principal': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'form-control',
                'data-max-size': '5MB'
            }),
            'edad_aproximada': forms.NumberInput(attrs={'min': '0'}),
            'peso': forms.NumberInput(attrs={'min': '0', 'step': '0.01'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar etiquetas
        self.fields['nombre'].label = 'Nombre del Peludo'
        self.fields['tipo'].label = 'Especie'
        self.fields['edad_aproximada'].label = 'Edad Aproximada (meses)'
        self.fields['peso'].label = 'Peso (kg)'
        self.fields['estado_adopcion'].label = 'Estado de Adopción'
        self.fields['fecha_ingreso'].label = 'Fecha de Ingreso a la Fundación'
        self.fields['imagen_principal'].label = 'Foto Principal del Peludo'
        
        # Añadir ayuda
        self.fields['imagen_principal'].help_text = 'Sube una foto clara y de buena calidad. La imagen se adaptará automáticamente al sitio web.'
        self.fields['descripcion'].help_text = 'Cuenta la historia del peludo y por qué sería un gran compañero.'
        self.fields['personalidad'].help_text = 'Describe cómo es su carácter y comportamiento.'
        self.fields['necesidades_especiales'].help_text = 'Si tiene alguna condición especial que requiera atención.'
        self.fields['estado_salud'].help_text = 'Información sobre su salud actual y tratamientos.'
    
    def clean_edad_aproximada(self):
        edad = self.cleaned_data.get('edad_aproximada')
        if edad is not None:
            if edad < 0:
                raise ValidationError("La edad no puede ser un número negativo.")
            if edad > 204: # 17 años en meses
                raise ValidationError("La edad máxima es de 17 años (204 meses).")
            if edad == 0:
                raise ValidationError("La edad debe ser al menos 1 mes.")
        return edad
    
    def clean_peso(self):
        peso = self.cleaned_data.get('peso')
        if peso is not None:
            if peso < 0:
                raise ValidationError("El peso no puede ser un número negativo.")
            if peso > 200:  # 200 kg como límite máximo razonable
                raise ValidationError("El peso no puede exceder 200 kg.")
        return peso
    
    def clean_fecha_ingreso(self):
        fecha_ingreso = self.cleaned_data.get('fecha_ingreso')
        if fecha_ingreso and fecha_ingreso < date.today():
            raise ValidationError("La fecha de ingreso no puede ser una fecha pasada.")
        return fecha_ingreso
    
    def clean_imagen_principal(self):
        imagen = self.cleaned_data.get('imagen_principal')
        if not imagen:
            raise ValidationError("La imagen principal es obligatoria.")
        # Aquí se podrían añadir más validaciones de tamaño, formato, etc.
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