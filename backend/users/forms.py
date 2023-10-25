from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CustomUserCreationForm(UserCreationForm):
    """
    Добавляет поле email в стандартную форму
    регистрации пользователя UserCreationForm из
    django.contrib.auth.forms.
    """

    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    labels = {
        'username': 'Имя пользователя',
        'email': 'Email',
        'password1': 'Пароль',
        'password2': 'Подтверждение пароля',
    }