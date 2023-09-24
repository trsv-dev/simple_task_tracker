from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


User = get_user_model()

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
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


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
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время создания'
    )
    deadline = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дедлайн'
    )
    tags = models.ManyToManyField(
        Tags,
        blank=True,
        through='TaskTag',
        related_name='tasks',
        verbose_name='Тег',
        help_text='Выберите подходящий тег'
    )

    def add_only_unique_tags(self, tags_list):
        for tag_name in tags_list:
            tag, create = Tags.objects.get_or_create(tag=tag_name)

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


class TaskTag(models.Model):
    """
    Модель 'многие ко многим' для сопоставления
    заданий и тегов.
    """

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        verbose_name='Задача'

    )
    tag = models.ForeignKey(
        Tags,
        on_delete=models.CASCADE,
        verbose_name='Тег'
    )

    class Meta:
        verbose_name = f'Связь'
        verbose_name_plural = 'Связи'

    def __str__(self):
        return f'задача - {self.task} и тег - {self.tag}'
