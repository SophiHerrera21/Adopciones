from django import template

register = template.Library()

@register.filter
def is_admin_email(email):
    """
    Filtro personalizado para verificar si un email es de administrador.
    Retorna True si el email termina en @huellas.com (case insensitive).
    """
    if not email:
        return False
    return email.lower().strip().endswith('@huellas.com') 