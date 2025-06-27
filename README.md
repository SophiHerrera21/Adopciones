# Sistema de Adopción de Mascotas - Luna & Lía

Un sistema completo de gestión de adopción de mascotas desarrollado en Django que permite a los usuarios registrarse, buscar mascotas, solicitar adopciones, realizar donaciones y gestionar todo el proceso desde un panel de administración.

## 🚀 Características Principales

### Para Usuarios
- ✅ **Registro e Inicio de Sesión**: Sistema completo de autenticación
- ✅ **Búsqueda de Mascotas**: Filtros avanzados por tipo, edad, tamaño, etc.
- ✅ **Solicitud de Adopción**: Formulario completo de pre-adopción
- ✅ **Sistema de Favoritos**: Guardar mascotas favoritas
- ✅ **Donaciones**: Múltiples tipos de donación (monetaria, insumos, servicios, especie)
- ✅ **Notificaciones**: Sistema de notificaciones en tiempo real
- ✅ **Perfil de Usuario**: Gestión de información personal
- ✅ **Reportes Personales**: Historial de donaciones y solicitudes

### Para Administradores
- ✅ **Panel de Administración**: Dashboard con estadísticas completas
- ✅ **Gestión de Mascotas**: Agregar, editar, eliminar mascotas
- ✅ **Búsquedas Múltiples**: Filtros avanzados para mascotas y donaciones
- ✅ **Gestión de Solicitudes**: Aprobar/rechazar solicitudes de adopción
- ✅ **Seguimiento de Mascotas**: Historial médico y de seguimiento
- ✅ **Gestión de Donaciones**: Categorías dinámicas y reportes
- ✅ **Reportes Generales**: PDFs con estadísticas completas
- ✅ **Correo Masivo**: Envío de comunicaciones a usuarios

## 🛠️ Tecnologías Utilizadas

- **Backend**: Django 4.2.7
- **Base de Datos**: SQLite (configurable para MySQL/PostgreSQL)
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Email**: SMTP con Gmail
- **Reportes**: ReportLab para PDFs
- **Gráficos**: Chart.js

## 📋 Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Git

## 🔧 Instalación

### 1. Clonar el Repositorio
```bash
git clone <url-del-repositorio>
cd isdhfpiuecl
```

### 2. Crear Entorno Virtual
```bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En macOS/Linux
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Base de Datos
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Crear Superusuario
```bash
python manage.py createsuperuser
```

### 6. Cargar Datos Iniciales
```bash
python manage.py crear_categorias_iniciales
python manage.py seed_data
```

### 7. Ejecutar el Servidor
```bash
python manage.py runserver
```

El sistema estará disponible en: http://127.0.0.1:8000/

## 📁 Estructura del Proyecto

```
isdhfpiuecl/
├── adopcion/                    # Aplicación principal
│   ├── models.py               # Modelos de datos
│   ├── views.py                # Vistas y lógica de negocio
│   ├── forms.py                # Formularios
│   ├── urls.py                 # Rutas de la aplicación
│   ├── templates/              # Plantillas HTML
│   ├── management/             # Comandos personalizados
│   └── migrations/             # Migraciones de base de datos
├── luna_lia_project/           # Configuración del proyecto
│   ├── settings.py             # Configuración de Django
│   ├── urls.py                 # Rutas principales
│   └── wsgi.py                 # Configuración WSGI
├── static/                     # Archivos estáticos
├── media/                      # Archivos subidos por usuarios
├── requirements.txt            # Dependencias del proyecto
└── manage.py                   # Script de gestión de Django
```

## 🔐 Configuración de Email

Para que el sistema de notificaciones funcione correctamente, configura las siguientes variables en `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'tu-contraseña-de-aplicación'
DEFAULT_FROM_EMAIL = 'Luna & Lia <tu-email@gmail.com>'
```

**Nota**: Para Gmail, necesitas usar una "Contraseña de aplicación" en lugar de tu contraseña normal.

## 👥 Roles de Usuario

### Usuario Regular
- Registrarse e iniciar sesión
- Buscar mascotas disponibles
- Solicitar adopciones
- Realizar donaciones
- Gestionar favoritos
- Ver notificaciones

### Administrador
- Acceso completo al panel de administración
- Gestión de mascotas
- Aprobar/rechazar solicitudes
- Gestionar donaciones
- Generar reportes
- Enviar correos masivos

## 🐕 Funcionalidades de Mascotas

### Información Registrada
- Nombre, tipo (perro/gato), raza
- Edad y fecha de nacimiento
- Sexo, tamaño, peso
- Estado de salud y vacunas
- Personalidad y necesidades especiales
- Múltiples fotos por mascota

### Estados de Adopción
- **Disponible**: Lista para adopción
- **En Proceso**: Tiene solicitudes pendientes
- **Adoptado**: Ya fue adoptada
- **No Disponible**: Temporalmente no disponible

## 💝 Sistema de Donaciones

### Tipos de Donación
1. **Monetaria**: Donaciones en efectivo con múltiples medios de pago
2. **Insumos**: Alimentos, medicamentos, accesorios, etc.
3. **Servicios**: Voluntariado, servicios profesionales
4. **En Especie**: Otros bienes o servicios

### Características
- Categorías dinámicas gestionables por administradores
- Frecuencias de donación (única, mensual, trimestral, etc.)
- Opción de donación anónima
- Comprobantes de pago
- Seguimiento de estado

## 📊 Reportes Disponibles

### Para Administradores
- Reporte de mascotas (PDF)
- Reporte de donaciones (PDF)
- Reporte de solicitudes (PDF)
- Reporte de actividad general (PDF)
- Estadísticas en tiempo real

### Para Usuarios
- Historial personal de donaciones
- Estado de solicitudes de adopción

## 🔍 Búsquedas y Filtros

### Mascotas
- Por nombre, raza, personalidad
- Por tipo, categoría, sexo, tamaño
- Por rango de edad y peso
- Por estado de adopción

### Donaciones
- Por donante (nombre, email)
- Por tipo y categoría
- Por rango de fechas y montos
- Por estado y frecuencia

## 📱 Notificaciones

El sistema incluye notificaciones automáticas para:
- Nuevas solicitudes de adopción
- Cambios de estado en solicitudes
- Nuevas donaciones
- Citas programadas
- Seguimiento de mascotas

## 🛡️ Seguridad

- Autenticación requerida para funcionalidades sensibles
- Validación de formularios
- Protección CSRF
- Decoradores de permisos para vistas administrativas
- Validación de archivos subidos

## 🚀 Despliegue

### Para Producción
1. Cambiar `DEBUG = False` en settings.py
2. Configurar `ALLOWED_HOSTS`
3. Configurar base de datos de producción (MySQL/PostgreSQL)
4. Configurar servidor web (Nginx + Gunicorn)
5. Configurar SSL/HTTPS

### Variables de Entorno Recomendadas
```bash
SECRET_KEY=tu-clave-secreta
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com
DATABASE_URL=tu-url-de-base-de-datos
EMAIL_HOST_USER=tu-email
EMAIL_HOST_PASSWORD=tu-contraseña
```

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico o preguntas sobre el sistema, contacta a:
- Email: soporte@lunaylia.com
- Teléfono: +57 XXX XXX XXXX

## 🎯 Roadmap

### Próximas Funcionalidades
- [ ] App móvil nativa
- [ ] Integración con redes sociales
- [ ] Sistema de chat en tiempo real
- [ ] Geolocalización de mascotas
- [ ] Integración con veterinarias
- [ ] Sistema de voluntariado avanzado
- [ ] API REST para integraciones externas

---

**Desarrollado con ❤️ para ayudar a las mascotas a encontrar su hogar para siempre.** 