from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


class Profile(models.Model):
    """Класс профиля."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(
        default='--пусто--',
        null=True,
        blank=True,
        verbose_name='Кратко о себе'
    )
    avatar = models.ImageField(
        null=True,
        blank=True,
        upload_to='images/avatars',
        verbose_name='Аватар',
        help_text='Добавить аватар'
    )

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f'Профиль {self.user}'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Автоматическое создание связи User и Profile при создании пользователя.
    """

    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Автоматическое сохранение изменений связи User и Profile.
    """

    instance.profile.save()
