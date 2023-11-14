import re
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from task_tracker.settings import TASKS_IN_PROFILE_PAGE
from task_tracker.settings import TEMPLATES_DIR
from tracker.forms import TaskCreateForm, CommentForm
from tracker.models import Task, Comment
from tracker.serializers import TaskSerializer, UserSerializer
from tracker.utils import send_email_about_closer_deadline
from tracker.utils import send_email_message

templates = {
    'create_task_template':
        f'{TEMPLATES_DIR}/email_templates/task_mail.html',
    'delete_task_template':
        f'{TEMPLATES_DIR}/email_templates/delete_task_mail.html',
    'reassigned_task_template':
        f'{TEMPLATES_DIR}/email_templates/reassigned_to_mail.html',
    'deadline_template':
        f'{TEMPLATES_DIR}/email_templates/deadline_mail.html',
    'message_to_mentioned_user':
        f'{TEMPLATES_DIR}/email_templates/message_to_mentioned_user.html'
}


def check_rights_to_task(username, task):
    """
    Проверяем, является ли пользователь автором задачи,
    админом или ответственным за задачу.
    """

    return (
            username == task.author or
            username.is_staff or
            username == task.assigned_to
    )


def index(request):
    """Отображение главной страницы."""

    tasks = Task.objects.all()
    context = {'tasks': tasks}
    return render(request, 'base.html', context)


def profile(request, user):
    """Отображение профиля пользователя."""

    profile_user = get_object_or_404(User, username=user)
    tasks = Task.objects.filter(assigned_to=profile_user).order_by('deadline')

    paginator = Paginator(tasks, TASKS_IN_PROFILE_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'username': profile_user,
        'tasks': tasks,
        'page_obj': page_obj
    }

    return render(request, 'tasks/profile.html', context)


def task_detail(request, pk):
    """Отображение деталей задачи."""

    task = get_object_or_404(Task, pk=pk)
    comments = Comment.objects.filter(task=task)
    form = CommentForm(request.POST)

    # Задел на будущее (вложенные комментарии и ответы на них).
    # parent_comments = comments.filter(parent_comment=None)
    context = {
        'task': task,
        'comments': comments,
        # 'parent_comments': parent_comments,
        'form': form

    }

    return render(request, 'tasks/task_detail.html', context)


@login_required
def create_task(request):
    """Создание задачи."""

    username = request.user
    all_users = User.objects.all()
    form = TaskCreateForm(request.POST or None)

    context = {
        'form': form,
        'current_user': username,
        'all_users': all_users,
    }

    if form.is_valid():
        task = form.save(commit=False)
        task.author = username
        form.save()

        assigned_to_email = task.assigned_to.email
        task_instance = Task.objects.get(id=task.pk)
        serializer = TaskSerializer(
            task_instance, context={'request': request}
        )
        serialized_data = serializer.data

        # Изменить на желаемое время напоминания о дедлайне,
        # пока для проверки стоит напоминание за 5 минут.
        eta_time = task.deadline - timedelta(minutes=5)

        send_email_message.apply_async(
            kwargs={
                'email': assigned_to_email,
                'template': templates['create_task_template'],
                'context': serialized_data,
            },
            countdown=5
        )

        # send_email_message.apply_async(
        #     kwargs={
        #         'email': assigned_to_email,
        #         'template': templates['deadline_template'],
        #         'context': serialized_data
        #     },
        #     eta=eta_time
        # )

        # send_email_about_closer_deadline()

        return redirect('tracker:index')
    return render(request, 'tasks/create.html', context)


@login_required
@transaction.atomic
def edit_task(request, pk):
    """Редактирование задачи."""

    username = request.user
    all_users = User.objects.all()
    task = get_object_or_404(Task, pk=pk)
    previous_assigned_to_username = task.assigned_to.username
    previous_deadline = task.deadline

    if check_rights_to_task(username, task) is False:
        return redirect('tracker:index')

    form = TaskCreateForm(request.POST or None, instance=task)

    if form.is_valid():
        task = form.save(commit=False)
        new_assigned_to = form.cleaned_data.get('assigned_to')
        new_deadline = form.cleaned_data.get('deadline')

        if new_deadline != previous_deadline:

            task.is_notified = False

        if new_assigned_to.username != previous_assigned_to_username:

            task.assigned_to = new_assigned_to
            assigned_to_email = new_assigned_to.email

            task_instance = Task.objects.get(id=task.pk)
            serializer = TaskSerializer(
                task_instance, context={'request': request}
            )
            serialized_data = serializer.data

            serialized_data[
                'previous_assigned_to_username'
            ] = previous_assigned_to_username

            send_email_message.apply_async(
                kwargs={
                    'email': assigned_to_email,
                    'template': templates['reassigned_task_template'],
                    'context': serialized_data,
                },
                countdown=5
            )

            return redirect('tracker:index')

        form.save()

    context = {
        'task': task,
        'form': form,
        'all_users': all_users
    }

    return render(request, 'tasks/create.html', context)


@login_required
@require_POST
def delete_task(request, pk):
    """Удаление задачи."""

    username = request.user
    task = get_object_or_404(Task, pk=pk)

    if check_rights_to_task(username, task) is False:
        return redirect('tracker:index')

    assigned_to_email = task.assigned_to.email

    task_instance = task
    serializer = TaskSerializer(task_instance, context={'request': request})
    serialized_data = serializer.data
    serialized_data['username'] = username.username

    task.delete()

    send_email_message.apply_async(
        kwargs={
            'email': assigned_to_email,
            'template': templates['delete_task_template'],
            'context': serialized_data,
        },
        countdown=5
    )

    return redirect('tracker:index')


@login_required
def mark_as_done(request, pk):
    """Пометить задачу как выполненную."""

    username = request.user
    task = Task.objects.get(pk=pk)
    task.previous_status = task.status
    task.is_done = True
    task.status = 'Выполнено'
    task.done_by = username
    task.done_by_time = timezone.now()
    task.save()
    return redirect('tracker:index')


@login_required
def mark_as_undone(request, pk):
    """Пометить задание как невыполненное."""

    task = Task.objects.get(pk=pk)
    if task.is_done:
        task.is_done = False
        task.status = task.previous_status
        task.done_by_time = None
        task.done_by = None
        task.save()
        return redirect('tracker:index')


@login_required
def create_comment(request, task_pk):
    """Создание комментария."""

    form = CommentForm(request.POST or None)
    task = get_object_or_404(Task, pk=task_pk)

    context = {
        'form': form,
        'task': task
    }

    if form.is_valid():
        comment = form.save(commit=False)
        comment.task = task
        comment.author = request.user
        form.save()

        notify_mentioned_users(request, comment.text, comment.task)

        # parent_comment_id = request.POST.get('parent_comment')
        # if parent_comment_id:
        #     parent_comment = get_object_or_404(Comment, pk=parent_comment_id)
        #     comment.parent_comment = parent_comment
        #     comment.save()

        return redirect('tracker:detail', pk=task.pk)
    return render(request, 'tasks/create_comment.html', context)


@login_required
def edit_comment(request, pk):
    """Редактирование комментария."""

    pass


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


def notify_mentioned_users(request, comment_text, comment_task):
    """
    Если в комментарии пользователя указали через @username
    присылает уведомление на электронную почту об упоминании.
    """

    search_pattern = re.compile(r'@(\w+)')
    mentioned_usernames = search_pattern.findall(comment_text)

    task_instance = comment_task

    for username in mentioned_usernames:
        user = get_object_or_404(User, username=username)
        user_email = user.email

        # Получаем данные username из сериализатора, иначе Celery не пропустит
        # несериализованные данные.
        user_instance = user
        serializer = UserSerializer(
            user_instance, context={'request': request}
        )
        username = serializer.data['username']

        # Получаем данные комментария из сериализатора,
        # иначе Celery не пропустит несериализованные данные.
        serializer = TaskSerializer(
            task_instance, context={'request': request}
        )
        comment_task = serializer.data['title']
        task_link = serializer.data['link']

        comment_author = request.user.username

        context = {
            'username': username,
            'comment_text': comment_text,
            'comment_task': comment_task,
            'comment_author': comment_author,
            'task_link': task_link
        }

        send_email_message.apply_async(
            kwargs={
                'email': user_email,
                'template': templates['message_to_mentioned_user'],
                'context': context
            },
            countdown=5
        )
