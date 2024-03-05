from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from users.forms import CustomUserCreationForm, UserEditForm, ProfileEditForm
from users.models import Profile


class RegisterView(CreateView):
    """Класс регистрации пользователей."""

    form_class = CustomUserCreationForm
    template_name = 'register.html'
    success_url = reverse_lazy('users:login')


def edit_profile(request):
    """Редактирование профиля."""

    user = request.user
    profile = Profile.objects.select_related('user').get(user=user)

    user_edit_form = UserEditForm(request.POST or None, instance=user)
    profile_edit_form = ProfileEditForm(
        request.POST or None, request.FILES or None, instance=profile
    )

    if user_edit_form.is_valid() and profile_edit_form.is_valid():
        user_edit_form.save()
        profile_edit_form.save()

        return redirect('tracker:profile', user=user)

    context = {
        'user_edit_form': user_edit_form,
        'profile_edit_form': profile_edit_form,
        'user': user
    }

    return render(request, 'users/edit_profile.html', context)
