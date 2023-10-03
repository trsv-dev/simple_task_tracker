from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView


class RegisterView(CreateView):
    """Класс регистрации пользователей."""

    form_class = UserCreationForm
    template_name = 'register.html'
    success_url = reverse_lazy('users:login')
