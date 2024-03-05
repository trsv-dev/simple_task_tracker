from django.contrib.auth.views import (LoginView, LogoutView,
                                       PasswordResetView,
                                       PasswordResetDoneView,
                                       PasswordResetConfirmView,
                                       PasswordResetCompleteView,
                                       PasswordChangeView,
                                       PasswordChangeDoneView)
from django.urls import path

from users.views import RegisterView, edit_profile

app_name = 'users'

urlpatterns = [
    path(
        'edit_profile/', edit_profile, name='edit_profile'
    ),
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
    path(
        'password_change/',
        PasswordChangeView.as_view(template_name='users/password_change.html'),
        name='password_change'
    ),
    path(
        'password_change/done/',
        PasswordChangeDoneView.as_view(
            template_name='users/password_change_done.html'
        )
    ),
    path(
        'password_reset/',
        PasswordResetView.as_view(template_name='users/password_reset.html'),
        name='password_reset'
    ),
    path(
        'password_reset/done/',
        PasswordResetDoneView.as_view(
            template_name='users/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        PasswordResetConfirmView.as_view(
            template_name='users/password_reset_confirm.html'
        ),
        name='password_reset_confirm',
    ),
    path(
        'reset/done/',
        PasswordResetCompleteView.as_view(
            template_name='users/password_reset_complete.html',
        ),
        name='password_reset_complete'
    ),
]
