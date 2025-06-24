from django.contrib import admin
from .models import (
    Usuario, Mascota, FotoMascota, SolicitudAdopcion, 
    SeguimientoAdopcion, Favorito, Donacion, Mensaje, ConfiguracionSitio, SeguimientoMascota
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
admin.site.register(SeguimientoAdopcion)
admin.site.register(Favorito)
