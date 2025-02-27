from django.shortcuts import redirect

class CambiarClaveMiddleware:
    """
    Middleware para forzar el cambio de contraseña si cambiarClave es True.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.cambiarClave and request.path != '/cambiar_clave/':
            return redirect('cambiar_clave')
        return self.get_response(request)
