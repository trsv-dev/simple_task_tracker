from django.shortcuts import render, get_object_or_404, redirect

from comments.models import Comment
from likes.models import Likes


def add_like(request, pk):
    """Добавление лайка к комментарию."""

    user = request.user
    comment = get_object_or_404(Comment, pk=pk)
    task_pk = comment.task.pk

    if not user.is_authenticated:
        return redirect('users:login')

    if user is not comment.author:
        Likes.objects.create(comment=comment, user=user)

    return redirect('tracker:detail', pk=task_pk)


def delete_like(request, pk):
    """Удаление лайка."""

    user = request.user
    comment = get_object_or_404(Comment, pk=pk)
    task_pk = comment.task.pk

    if not user.is_authenticated:
        return redirect('users:login')

    liked = Likes.objects.filter(user=user, comment=comment)

    if user is not comment.author and liked.exists():
        liked.delete()

    return redirect('tracker:detail', pk=task_pk)
