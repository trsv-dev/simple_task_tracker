from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User

from users.models import Profile


class CustomUserCreationForm(UserCreationForm):
    """
    Добавляет поле email в стандартную форму
    регистрации пользователя UserCreationForm из
    django.contrib.auth.forms.
    """

    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username',
                  'email', 'password1', 'password2']

    labels = {
        'username': 'Имя пользователя',
        'email': 'Email',
        'password1': 'Пароль',
        'password2': 'Подтверждение пароля',
    }


class UserEditForm(UserChangeForm):
    """Форма редактирования информации пользователя."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def __init__(self, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        # Убираем поле пароля
        del self.fields['password']


class ProfileEditForm(forms.ModelForm):
    """Форма редактирования информации профиля."""

    class Meta:
        model = Profile
        fields = ['bio', 'telegram_username', 'avatar', 'is_private']

        widgets = {
            'is_private': forms.CheckboxInput(
                attrs={'class': 'checkbox'}
            )
        }
