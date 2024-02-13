from urllib.parse import quote_plus

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from comments.forms import CommentForm, CommentImageForm
from comments.models import Comment
from images.views import handle_images
from tracker.models import Task
from tracker.utils import search_mentioned_users, notify_mentioned_users
from tracker.views import get_all_usernames_list


@login_required
def create_comment(request, task_pk):
    """Создание комментария."""

    comment_form = CommentForm(request.POST or None)
    image_form = CommentImageForm(request.POST or None, request.FILES or None)
    task = get_object_or_404(Task, pk=task_pk)

    context = {
        'comment_form': comment_form,
        'image_form': image_form,
        'task': task
    }

    if comment_form.is_valid():
        comment = comment_form.save(commit=False)
        comment.task = task
        comment.author = request.user

        # Экранируем символы с помощью quote_plus, т.к. в комментах может
        # быть код.
        comment_text = quote_plus(comment.text)
        # comment_form.save()
        comment.save()
        handle_images(request, comment, Comment)

        highlighted_comment_id = comment.pk
        all_usernames_list = get_all_usernames_list()
        list_of_mentioned_users = search_mentioned_users(comment_text,
                                                         all_usernames_list)

        if len(list_of_mentioned_users) > 0:
            notify_mentioned_users(request, comment_text,
                                   highlighted_comment_id,
                                   list_of_mentioned_users,
                                   comment.task)

        parent_id = request.POST.get('parent')

        if parent_id:
            parent = get_object_or_404(Comment, pk=parent_id)
            comment.parent = parent

            comment.save()

        return redirect('tracker:detail', pk=task.pk)
    return render(request, 'tasks/create_comment.html', context)


@login_required
def edit_comment(request, pk):
    """Редактирование комментария."""

    comment = get_object_or_404(Comment, pk=pk)
    task = comment.task
    user = request.user
    form = CommentForm(request.POST or None, instance=comment)

    if user != comment.author:
        return redirect('tracker:detail', pk=task.pk)

    if form.is_valid():
        form.save()
        handle_images(request, comment, Comment)

    return redirect('tracker:detail', pk=task.pk)


@login_required
@require_POST
def delete_comment(request, pk):
    """Удаление комментария."""

    comment = get_object_or_404(Comment, pk=pk)
    user = request.user
    task = comment.task

    if user != comment.author:
        return redirect('tracker:detail', pk=task.pk)

    comment.delete()

    return redirect('tracker:detail', pk=task.pk)
