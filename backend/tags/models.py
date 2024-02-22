from django.core.validators import RegexValidator
from django.db import models

from tracker.models import Task


class Tags(models.Model):
    """Класс тегов."""

    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Тег'
    )
    slug = models.CharField(
        max_length=100,
        unique=True,
        blank=False,
        validators=(RegexValidator(
            regex=r'^[-a-zA-Z0-9_]+$',
            message='В слаге содержится недопустимый символ'
            ),
        ),
        verbose_name='Слаг'
    )

    class Meta:
        verbose_name = 'Создать тег'
        verbose_name_plural = 'Создать теги'

    def __str__(self):
        return self.name


class TaskTag(models.Model):
    """Модель для сопоставления заданий и тегов."""

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='tags',
        verbose_name='Задача',
        help_text='Выберите задачу'

    )
    tag = models.ForeignKey(
        Tags,
        on_delete=models.CASCADE,
        verbose_name='Тег',
        help_text='Выберите тег'
    )

    class Meta:
        verbose_name = 'Присвоить тег'
        verbose_name_plural = 'Присвоить теги'
        constraints = (
            models.UniqueConstraint(
                fields=('task', 'tag'),
                name='unique_task_tag'
            ),
        )

    def __str__(self):
        return f'Задаче "{self.task}" присвоен тег "{self.tag}"'
