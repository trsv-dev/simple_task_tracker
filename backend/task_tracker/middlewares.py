from django.shortcuts import redirect
from django.urls import reverse


class AuthMiddleware:
    """Middleware для предотвращения доступа к сайту без авторизации."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        reset_password_base_url = '/auth/reset/'

        if (not request.user.is_authenticated and
                request.path.startswith(reset_password_base_url)):
            # Если пользователь не аутентифицирован и запрашиваемый путь
            # начинается с базового URL для сброса пароля,
            # то не перенаправляем его на страницу входа
            response = self.get_response(request)
            return response

        excluded_paths = [
            reverse('users:login'),
            reverse('users:password_reset'),
            reverse('users:password_reset_done'),
            reverse('users:password_reset_confirm', args=[1, 'token']),
            reverse('users:password_reset_complete'),
            reverse('users:logout')
        ]

        if (not request.user.is_authenticated and
                request.path not in excluded_paths):
            # Если пользователь не аутентифицирован и не находится
            # на исключенных страницах, перенаправляем его на страницу входа
            return redirect(reverse('users:login'))

        response = self.get_response(request)
        return response
