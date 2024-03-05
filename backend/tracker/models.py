from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from images.models import BaseImage
from users.models import User

PENDING = 'Ожидает выполнения'
IN_PROGRESS = 'В процессе выполнения'
DONE = 'Выполнено'

STATUS = [(PENDING, 'Ожидает выполнения'),
          (IN_PROGRESS, 'В процессе выполнения'),
          (DONE, 'Выполнено')]

HIGH = 'Высокий'
MEDIUM = 'Средний'
LOW = 'Низкий'

PRIORITY = [(HIGH, 'Высокий'),
            (MEDIUM, 'Средний'),
            (LOW, 'Низкий')]


class Task(models.Model):
    """Класс заданий."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Автор',
        help_text='Выберите автора'
    )
    title = models.CharField(
        max_length=120,
        verbose_name='Название',
        help_text='Введите название задачи',
    )
    description = models.TextField(
        verbose_name='Описание',
        help_text='Введите описание задачи'
    )

    priority = models.CharField(
        max_length=120,
        choices=PRIORITY,
        default=LOW,
        blank=False,
        verbose_name='Приоритет',
        help_text='Установите приоритет'
    )
    status = models.CharField(
        max_length=120,
        choices=STATUS,
        default=PENDING,
        blank=False,
        verbose_name='Статус',
        help_text='Выберите статус'
    )
    previous_status = models.CharField(
        max_length=120,
        choices=STATUS,
        blank=True,
        null=True,
        verbose_name='Предыдущий статус',
        help_text='Выберите предыдущий статус'
    )
    assigned_to = models.ForeignKey(
        User,
        default=User,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        verbose_name='Исполнитель',
        help_text='Выберите пользователя, который '
                  'будет ответственен за задачу.'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время создания'
    )
    deadline = models.DateTimeField(
        default=timezone.now,
        validators=(
            MinValueValidator(
                timezone.now, message='Дедлайн не может быть в прошлом!'
            ),
        ),
        verbose_name='Дедлайн'
    )
    deadline_reminder = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Когда напомнить о дедлайне',
        help_text='Если не заполнять, то напоминание придет за сутки до '
                  'дедлайна. На отрезках менее суток лучше заполнять вручную'
    )
    is_notified = models.BooleanField(
        default=False,
        verbose_name='Уведомлен?',
        help_text='Уведомлен ли пользователь о приближении дедлайна'
    )
    is_done = models.BooleanField(
        default=False,
        verbose_name='Выполнено',
        help_text='Отмечено ли задание как выполненное'
    )
    done_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='done_by',
        verbose_name='Выполнил(а)',
        help_text='Выберите пользователя, отметившего задачу выполненной'
    )
    done_by_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Время выполнения',
        help_text='Время, когда задача была отмечена выполненной'
    )

    def save(self, *args, **kwargs):

        temp_deadline_reminder = self.deadline_reminder

        # Отключаем проверку даты и времени напоминания о дедлайне если
        # мы просто ходим отметить задачу как выполненную.

        skip_deadline_reminder_check = kwargs.pop(
            'skip_deadline_reminder_check', False
        )

        if not skip_deadline_reminder_check:
            if not temp_deadline_reminder:
                self.deadline_reminder = self.deadline - timedelta(hours=24)
            if self.deadline_reminder > self.deadline:
                raise ValidationError(
                    'Напоминание о дедлайне не может быть позже дедлайна!'
                )
            if (self.deadline_reminder < timezone.now()
                    and not self.is_notified):
                raise ValidationError(
                    'Это задача, по которой еще не приходило напоминание '
                    'пользователю. Если сделать дату напоминания в прошлом, '
                    'то уведомление не придёт!'
                )
            if self.deadline_reminder < timezone.now():
                raise ValidationError(
                    'Напоминание о дедлайне не может быть в прошлом!'
                )
            if self.deadline < timezone.now():
                raise ValidationError(
                    'Дедлайн не может быть в прошлом!'
                )
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'

    def __str__(self):
        return self.title


class TaskImage(BaseImage):
    """Модель изображений к задачам."""

    task = models.ForeignKey(
        'Task',
        related_name='images',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Изображение'
        verbose_name_plural = 'Изображения'

    def __str__(self):
        return f'Изображение для задачи "{self.task.title}"'
