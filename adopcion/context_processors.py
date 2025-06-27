from .models import Notificacion

def notificaciones_context(request):
    """Context processor para agregar información de notificaciones al contexto global"""
    context = {}
    
    if request.user.is_authenticated:
        # Contar notificaciones no leídas
        notificaciones_no_leidas = Notificacion.objects.filter(
            usuario=request.user, 
            leida=False
        ).count()
        
        context['notificaciones_no_leidas'] = notificaciones_no_leidas
        context['tiene_notificaciones'] = notificaciones_no_leidas > 0
    
    return context 