from django.utils import timezone
from django.db import models

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
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время создания'
    )
    deadline = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дедлайн'
    )

    def get_priority_color(self):
        """Выбор цвета в зависимости от приоритета."""

        if self.priority == HIGH:
            return 'red'
        elif self.priority == MEDIUM:
            return 'blue'
        return 'green'

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'

    def __str__(self):
        return self.title
