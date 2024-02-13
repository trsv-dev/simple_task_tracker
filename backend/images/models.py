from django.db import models


class BaseImage(models.Model):
    """Базовая абстрактная модель изображений."""

    image = models.ImageField(
        null=True,
        blank=True,
        upload_to='images',
        verbose_name='Изображение',
        help_text='Добавьте изображение'
    )

    class Meta:
        abstract = True
