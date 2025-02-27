from django.http import HttpResponseForbidden
from functools import wraps

def role_required(allowed_roles):
    """
    Decorador para permitir acceso a usuarios con roles específicos.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated or request.user.IdRol.Descripcion not in allowed_roles:
                return HttpResponseForbidden("No tienes permiso para acceder a esta página.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
