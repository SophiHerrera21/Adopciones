from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test
from functools import wraps
from django.shortcuts import redirect
from django.conf import settings
from django.utils.encoding import force_str

def admin_required(function=None, redirect_field_name=None, login_url='login'):
    """
    Decorador que comprueba que el usuario es un administrador.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.rol == 'administrador',
        login_url=login_url
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def admin_email_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        email = force_str(request.user.email).strip().lower().replace(' ', '')
        if not email.endswith('@huellas.com'):
            return redirect('inicio')
        return view_func(request, *args, **kwargs)
    return _wrapped_view 