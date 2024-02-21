from django.db import models

from tracker.models import Task, User


class Favorites(models.Model):
    """Модель избранного. """

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        verbose_name='Избранное',
        help_text='Выберите задачу'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
        help_text='Выберите пользователя'
    )
    added_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время добавления в избранное'
    )

    class Meta:
        ordering = ('-added_time',)
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'task'),
                name='unique_user_task_favorites'
            ),
        )

    def __str__(self):
        return (f'{self.user} добавил в избранное задачу '
                f'"{self.task.title[:30]}"')
