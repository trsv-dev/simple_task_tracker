from copy import deepcopy
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.core.serializers import serialize
from django.db import transaction
from django.db.models import Model
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from task_tracker.settings import TASKS_IN_PROFILE_PAGE
from tracker.forms import TaskCreateForm, CommentForm
from tracker.models import Task, Comment
from tracker.serializers import TaskSerializer
from tracker.utils import send_email_message, notify_mentioned_users, templates


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


def check_deadline_or_deadline_reminder(new_deadline, new_deadline_reminder):
    """
    Проверка дедлайна и времени напоминания о дедлайне.
    Дедлайн не должен быть в прошлом.
    Напоминание о дедлайне не должно быть в прошлом.
    Напоминание о дедлайне не должно быть позже дедлайна.
    """

    return (
            new_deadline > timezone.now() and
            new_deadline_reminder > timezone.now() and
            new_deadline_reminder < new_deadline
    )


def is_title_description_priority_status_changed(original_task, form):
    """
    Проверяем что изменения есть только в заголовке, описании,
    приоритете и статусе.
    """

    form_data = form.cleaned_data

    return (((form_data.get('status') != original_task.status or
             form_data.get('priority') != original_task.priority) or
            (form_data.get('title') != original_task.title or
             form_data.get('description') != original_task.description)) and
            form_data.get('assigned_to').username == original_task.assigned_to.username)


def is_deadline_deadline_reminder_user_changed(request, original_task,
                                               task, new_deadline,
                                               new_deadline_reminder,
                                               new_assigned_to):
    """
    Проверяем, были ли изменения в дедлайне, напоминании о
    дедлайне и пользователе.
    """

    if (new_deadline != original_task.deadline and
            check_deadline_or_deadline_reminder(
                new_deadline, new_deadline_reminder
            )):
        task.deadline = new_deadline
        assigned_to_email = new_assigned_to.email
        universal_mail_sender(request, task, assigned_to_email,
                              templates['new_deadline_template'], )

        task.is_notified = False

    if new_deadline_reminder != original_task.deadline_reminder:
        task.deadline_reminder = new_deadline_reminder
        task.is_notified = False

    if (new_assigned_to.username != original_task.assigned_to.username and
            check_deadline_or_deadline_reminder(
                new_deadline, new_deadline_reminder
            )):
        # Т.к. юзер уже поменялся на нового после сохранения формы
        # form.save(commit=False) - просто берем его почту.
        assigned_to_email = task.assigned_to.email

        universal_mail_sender(
            request,
            task,
            assigned_to_email,
            templates['reassigned_task_template'],
            priority=0,
            queue='fast_queue',
            previous_assigned_to_username=original_task.assigned_to.username
        )


def save_task_and_handle_form_errors(form, all_users, task=None):
    """
    Попытка сохранить задачу и вывод ошибок для дальнейшего
    отображения в форме при неудачном сохранении.
    """

    try:
        form.save()
        return None
    except ValidationError as e:
        form.add_error(None, e)
        if task:
            context = {
                'form': form,
                'all_users': all_users
            }
        else:
            context = {
                'task': task,
                'form': form,
                'all_users': all_users
            }
        return context


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
    deadline_reminder_str = request.POST.get('deadline_reminder')

    context = {
        'form': form,
        'current_user': username,
        'all_users': all_users,
    }

    if form.is_valid():
        task = form.save(commit=False)
        task.author = username

        # Если поле даты/времени напоминания о дедлайне не было заполнено,
        # то оно придет за сутки до дедлайна.

        if not deadline_reminder_str:
            task.deadline_reminder = task.deadline - timedelta(hours=24)

        # А если заполнено, то придет когда указано в форме.
        # Преобразование строки в datetime с учетом временной зоны.

        else:
            deadline_reminder_dt = datetime.strptime(
                deadline_reminder_str, '%Y-%m-%dT%H:%M'
            )
            deadline_reminder_dt = timezone.make_aware(
                deadline_reminder_dt, timezone.get_current_timezone()
            )
            task.deadline_reminder = deadline_reminder_dt

        result = save_task_and_handle_form_errors(form, all_users)

        if result:
            context.update(result)
            return render(request, 'tasks/create.html', context)

        assigned_to_email = task.assigned_to.email

        universal_mail_sender(request, task, assigned_to_email,
                              templates['create_task_template'])

        return redirect('tracker:index')
    return render(request, 'tasks/create.html', context)


@login_required
@transaction.atomic
def edit_task(request, pk):
    """Редактирование задачи."""

    username = request.user
    all_users = User.objects.all()
    task = get_object_or_404(Task, pk=pk)
    original_task = deepcopy(task)

    if not check_rights_to_task(username, task):
        return redirect('tracker:index')

    form = TaskCreateForm(request.POST or None, instance=task)

    context = {
        'task': task,
        'form': form,
        'all_users': all_users
    }

    if form.is_valid():
        task = form.save(commit=False)
        new_assigned_to = form.cleaned_data.get('assigned_to')
        new_deadline = form.cleaned_data.get('deadline')
        new_deadline_reminder = form.cleaned_data.get('deadline_reminder')

        if is_title_description_priority_status_changed(original_task, form):
            task.save(skip_deadline_reminder_check=True)
            return redirect('tracker:detail', pk=task.id)

        else:
            is_deadline_deadline_reminder_user_changed(request, original_task,
                                                       task, new_deadline,
                                                       new_deadline_reminder,
                                                       new_assigned_to)

            result = save_task_and_handle_form_errors(form, all_users, task)

            if result:
                context.update(result)
                return render(
                    request, 'tasks/create.html', context
                )

            return redirect('tracker:detail', pk=task.id)

    return render(request, 'tasks/create.html', context)


@login_required
@require_POST
def delete_task(request, pk):
    """Удаление задачи."""

    username = request.user
    task = get_object_or_404(Task, pk=pk)

    if not check_rights_to_task(username, task):
        return redirect('tracker:index')

    assigned_to_email = task.assigned_to.email

    # Чтобы можно было удалить задачу, но передать в функцию
    # отправки почты данные о задаче - сохраняем ее "слепок".

    # task_data = {
    #     'id': task.id,
    #     'title': task.title,
    #     'description': task.description,
    #     'assigned_to': task.assigned_to,
    #     'author': task.author,
    #     'deadline': task.deadline
    # }

    # "Слепок" делаем с помощью deepcopy, которая временно сохранит данные
    # экземпляра модели после того как экземпляр будет удалён.
    saved_task_data = deepcopy(task)

    task.delete()

    # Вместо экземпляра task передаем "слепок" saved_task_data, идентичный
    # экземпляру task.

    universal_mail_sender(request, saved_task_data, assigned_to_email,
                          templates['delete_task_template'])

    return redirect('tracker:index')


@login_required
def mark_as_done(request, pk):
    """Пометить задачу как выполненную."""

    username = request.user
    task = get_object_or_404(Task, pk=pk)
    task.previous_status = task.status
    task.is_done = True
    task.status = 'Выполнено'
    task.done_by = username
    task.done_by_time = timezone.now()
    # Отменяем проверку даты и времени напоминания о дедлайне в модели.
    task.save(skip_deadline_reminder_check=True)
    return redirect('tracker:index')


@login_required
def mark_as_undone(request, pk):
    """Пометить задание как невыполненное."""

    task = get_object_or_404(Task, pk=pk)
    if task.is_done:
        task.is_done = False
        task.status = task.previous_status
        task.done_by_time = None
        task.done_by = None
        # Отменяем проверку даты и времени напоминания о дедлайне в модели.
        task.save(skip_deadline_reminder_check=True)
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

    comment = get_object_or_404(Comment, pk=pk)
    task = comment.task
    user = request.user
    form = CommentForm(request.POST or None, instance=comment)

    if user != comment.author:
        return redirect('tracker:detail', pk=task.pk)

    if form.is_valid():
        form.save()

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


def universal_mail_sender(request, task, assigned_to_email,
                          template, priority=9, queue='slow_queue', **kwargs):

    username = request.user

    serializer = TaskSerializer(task)
    serialized_data = serializer.data

    serialized_data['username'] = username.username

    if 'previous_assigned_to_username' in kwargs:
        serialized_data[
            'previous_assigned_to_username'
        ] = kwargs['previous_assigned_to_username']

    send_email_message.apply_async(
        kwargs={
            'email': assigned_to_email,
            'template': template,
            'context': serialized_data,
        },
        priority=priority,
        queue=queue,
        countdown=5
    )

# Раскомментировать если используем сериализатор DRF

# def universal_mail_sender(request, task, assigned_to_email,
#                           template, priority=9, queue='slow_queue', **kwargs):
#     """
#     Универсальная функция отправки сообщений о событиях, связанных с задачами.
#     """
#
#     username = request.user
#     task_instance = task
#     serializer = TaskSerializer(task_instance, context={'request': request})
#
#     serializer = TaskSerializer(task_instance, context={'request': request})
#     serialized_data = serializer.data
#
#     serialized_data['username'] = username.username
#
#     if 'previous_assigned_to_username' in kwargs:
#         serialized_data[
#             'previous_assigned_to_username'
#         ] = kwargs['previous_assigned_to_username']
#
#     send_email_message.apply_async(
#         kwargs={
#             'email': assigned_to_email,
#             'template': template,
#             'context': serialized_data,
#         },
#         priority=priority,
#         queue=queue,
#         countdown=5
#     )
