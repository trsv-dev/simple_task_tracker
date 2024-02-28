from django.db import models

from comments.models import Comment
from tracker.models import User


class Likes(models.Model):
    """Модель лайков. """

    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        verbose_name='Комментарий',
        help_text='Выберите комментарий'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='Пользователь',
        help_text='Выберите пользователя'
    )
    added_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время лайка'
    )

    class Meta:
        ordering = ('-added_time',)
        verbose_name = 'Лайк'
        verbose_name_plural = 'Лайки'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'comment'),
                name='unique_user_comment_likes'
            ),
        )

    def __str__(self):
        return (f'{self.user} лайкнул комментарий '
                f'"{self.comment.text[:30]}"')
