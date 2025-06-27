from django.contrib import admin
from .models import (
    Usuario, Mascota, FotoMascota, SolicitudAdopcion, 
    Favorito, Donacion, Mensaje, ConfiguracionSitio,
    HistorialMascota, CitaPreAdopcion, CategoriaDonacion, 
    Notificacion, SeguimientoMascota
)

# Para mejorar la visualización de las fotos en el admin de Mascota
class FotoMascotaInline(admin.TabularInline):
    model = FotoMascota
    extra = 1 # Muestra 1 campo para subir foto por defecto

@admin.register(Mascota)
class MascotaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'raza', 'sexo', 'estado_adopcion', 'fecha_ingreso')
    list_filter = ('estado_adopcion', 'tipo', 'sexo', 'esterilizado')
    search_fields = ('nombre', 'raza')
    inlines = [FotoMascotaInline]

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'nombre', 'apellido', 'rol', 'is_staff')
    list_filter = ('rol', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'nombre', 'apellido')

@admin.register(SolicitudAdopcion)
class SolicitudAdopcionAdmin(admin.ModelAdmin):
    list_display = ('mascota', 'usuario', 'estado_solicitud', 'fecha_solicitud')
    list_filter = ('estado_solicitud',)
    search_fields = ('mascota__nombre', 'usuario__username')

# Registrar los otros modelos para que sean visibles en el admin
admin.site.register(Donacion)
admin.site.register(Mensaje)
admin.site.register(ConfiguracionSitio)
admin.site.register(Favorito)

@admin.register(CategoriaDonacion)
class CategoriaDonacionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activa', 'fecha_creacion', 'donaciones_count']
    list_filter = ['activa', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion']
    ordering = ['-fecha_creacion']
    
    def donaciones_count(self, obj):
        return obj.donacion_set.count()
    donaciones_count.short_description = 'Donaciones'

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo', 'titulo', 'leida', 'fecha_creacion']
    list_filter = ['tipo', 'leida', 'fecha_creacion']
    search_fields = ['usuario__username', 'usuario__email', 'titulo', 'mensaje']
    ordering = ['-fecha_creacion']
    readonly_fields = ['fecha_creacion', 'fecha_lectura']

@admin.register(SeguimientoMascota)
class SeguimientoMascotaAdmin(admin.ModelAdmin):
    list_display = ['mascota', 'fecha_seguimiento', 'peso', 'estado_salud', 'administrador']
    list_filter = ['fecha_seguimiento', 'administrador']
    search_fields = ['mascota__nombre', 'estado_salud', 'observaciones']
    ordering = ['-fecha_seguimiento']
    readonly_fields = ['fecha_seguimiento']
