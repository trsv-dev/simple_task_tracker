from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from users.views import RegisterView

app_name = 'users'

urlpatterns = [
    path(
        'login/',
        LoginView.as_view(template_name='users/login.html'),
        name='login'
    ),
    path(
        'logout/',
        LogoutView.as_view(template_name='users/logout.html'),
        name='logout'
    ),
    path(
        'register/',
        RegisterView.as_view(template_name='users/register.html'),
        name='register'
    ),
]
