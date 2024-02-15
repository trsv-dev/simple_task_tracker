from django.db import models
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from images.models import BaseImage
from tracker.models import Task, User


class CommentImage(BaseImage):
    """Модель изображений к комментариям."""

    comment = models.ForeignKey(
        'Comment',
        related_name='images',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Изображение'
        verbose_name_plural = 'Изображения'

    def __str__(self):
        return f'Изображение для комментария "{self.comment.text[:30]}"'


class Comment(MPTTModel):
    """Класс древовидных комментариев к задаче."""

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Задача',
        help_text='Комментарий к задаче'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        help_text='Автор комментария'
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Введите текст комментария'
    )
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='Родительский комментарий',
        help_text='Введите ответ на комментарий'
    )

    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации комментария'
    )

    class MTTMeta:
        order_insertion_by = ('-created',)

    class Meta:
        ordering = ['-created']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        if self.parent:
            return (f'{self.author} ответил на комментарий '
                    f'"{self.parent.text}"')
        return (f'{self.author} прокомментировал задачу "{self.task.title}": '
                f'{self.text}')
