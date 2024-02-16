from datetime import timedelta
from urllib.parse import quote_plus

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from comments.forms import CommentForm, CommentImageForm
from comments.models import Comment
from images.views import handle_images
from tracker.models import Task
from tracker.utils import search_mentioned_users, notify_mentioned_users
from tracker.views import get_all_usernames_list, \
    save_task_and_handle_form_errors, get_profile


@login_required
# @cache_page(20)
def create_comment(request, task_pk):
    """Создание комментария."""

    image_form = CommentImageForm(request.POST or None, request.FILES or None)
    task = get_object_or_404(Task.objects.select_related('author',
                                                         'assigned_to',
                                                         'done_by'), pk=task_pk)

    comments = task.comments.select_related('author').prefetch_related('images')

    comment_form = CommentForm(request.POST or None)
    comment_texts = [comment.text for comment in comments]
    comments_with_expired_editing_time = []
    images_in_task = task.images.all()

    images_in_comments = [comment.images.all() for comment in comments]

    highlighted_comment_id = int(request.GET.get('highlighted_comment_id', 0))

    for comment in comments:
        if timezone.now() > (comment.created + timedelta(minutes=30)):
            comments_with_expired_editing_time.append(comment)

    all_usernames_list = get_all_usernames_list()
    # Из списка списков делаем плоский список пользователей.
    list_of_mentioned_users = sum([search_mentioned_users(
        comment_text, all_usernames_list
    ) for comment_text in comment_texts], [])
    # Создаем словарь: ключ - имя пользователя, значение - ссылка на профиль.
    usernames_profiles_links = {
        username: get_profile(username) for username in list_of_mentioned_users
    }

    context = {
        'comment_form': comment_form,
        'image_form': image_form,
        'task': task,
        'comments': comments,
        'comments_with_expired_editing_time':
            comments_with_expired_editing_time,
        'usernames_profiles_links': usernames_profiles_links,
        'images_in_task': images_in_task,
        'images_in_comments': images_in_comments,
        'highlighted_comment_id': highlighted_comment_id
    }

    if comment_form.is_valid():
        comment = comment_form.save(commit=False)
        comment.task = task
        comment.author = request.user

        # Экранируем символы с помощью quote_plus, т.к. в комментах может
        # быть код.
        comment_text = quote_plus(comment.text)

        result = save_task_and_handle_form_errors(request,
                                                  form=comment_form,
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

        parent_id = request.POST.get('parent')

        if parent_id:
            parent = get_object_or_404(Comment, pk=parent_id)
            comment.parent = parent

            comment.save()

        return redirect('tracker:detail', pk=task.pk)
    return render(request, 'comments/create_comment.html', context)


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
