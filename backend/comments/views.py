from urllib.parse import quote_plus

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from comments.forms import CommentForm, CommentImageForm
from comments.models import Comment
from tracker.models import Task
from tracker.utils import (search_mentioned_users,
                           notify_mentioned_users,
                           get_common_context,
                           get_all_usernames_list)
from tracker.views import save_obj_and_handle_form_errors


@login_required
def create_comment(request, task_pk):
    """Создание комментария."""

    task = get_object_or_404(
        Task.objects.select_related('author',
                                    'assigned_to',
                                    'done_by'), pk=task_pk
    )

    comments = task.comments.select_related('author').prefetch_related(
        'images'
    )
    context = get_common_context(request, task, comments)
    context['image_form'] = CommentImageForm(request.POST or None,
                                             request.FILES or None)

    if context['comment_form'].is_valid():
        comment = context['comment_form'].save(commit=False)
        comment.task = task
        comment.author = request.user

        parent_id = request.POST.get('parent')

        if parent_id:
            parent = get_object_or_404(Comment, pk=parent_id)
            comment.parent = parent

        # Экранируем символы с помощью quote_plus, т.к. в комментах может
        # быть код.
        comment_text = quote_plus(comment.text)

        result = save_obj_and_handle_form_errors(request,
                                                 form=context['comment_form'],
                                                 object=comment,
                                                 model=Comment)
        if result:
            context.update(result)
            return render(request, 'tasks/task_detail.html', context)

        highlighted_comment_id = comment.pk
        all_usernames_list = get_all_usernames_list()
        list_of_mentioned_users = search_mentioned_users(comment_text,
                                                         all_usernames_list)

        if len(list_of_mentioned_users) > 0:
            notify_mentioned_users(request, comment_text,
                                   highlighted_comment_id,
                                   list_of_mentioned_users,
                                   comment.task)

        return redirect('tracker:detail', pk=task.pk)
    return render(request, 'comments/create_comment.html', context)


@login_required
def edit_comment(request, pk):
    """Редактирование комментария."""

    comment = get_object_or_404(Comment, pk=pk)
    task = comment.task
    user = request.user
    comments = task.comments.select_related('author').prefetch_related(
        'images')

    context = get_common_context(request, task, comments)
    context['comment_form'] = CommentForm(
        request.POST or None, instance=comment
    )

    context['image_form'] = CommentImageForm(request.POST or None,
                                             request.FILES or None)

    if user != comment.author:
        return redirect('tracker:detail', pk=task.pk)

    if context['comment_form'].is_valid():
        result = save_obj_and_handle_form_errors(request,
                                                 form=context['comment_form'],
                                                 object=comment,
                                                 model=Comment)
        if result:
            context.update(result)
            return render(request, 'tasks/task_detail.html', context)

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
