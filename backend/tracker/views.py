from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from task_tracker.settings import TEMPLATES_DIR
from tracker.forms import TaskCreateForm
from tracker.models import Task
from tracker.serializers import TaskSerializer
from tracker.utils import (deadline_reminder_email,
                           send_email_message,)


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


def task_detail(request, pk):
    """Отображение деталей задачи."""

    task = Task.objects.get(pk=pk)
    context = {'task': task}
    return render(request, 'tasks/task_detail.html', context)


@login_required
def create_task(request):
    """Создание задачи."""

    username = request.user
    all_users = User.objects.all()
    form = TaskCreateForm(request.POST)

    template = f'{TEMPLATES_DIR}/email_templates/task_mail.html'

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

        eta_time = task.deadline - timedelta(minutes=5)

        send_email_message.apply_async(
            kwargs={
                'email': assigned_to_email,
                'template': template,
                'context': serialized_data,
            },
            countdown=5
        )

        deadline_reminder_email.apply_async(
            kwargs={
                'email': assigned_to_email,
                'context': serialized_data
            },
            eta=eta_time
        )

        return redirect('tracker:index')
    return render(request, 'tasks/create.html', context)


@login_required
def edit_task(request, pk):
    """Редактирование задачи."""

    username = request.user
    all_users = User.objects.all()
    task = get_object_or_404(Task, pk=pk)
    previous_assigned_to_username = task.assigned_to.username

    if check_rights_to_task(username, task) is False:
        return redirect('tracker:index')

    form = TaskCreateForm(request.POST, instance=task)

    if form.is_valid():
        task = form.save(commit=False)
        new_assigned_to_username = form.cleaned_data.get('assigned_to')

        if new_assigned_to_username != previous_assigned_to_username:
            task.assigned_to = new_assigned_to_username

        form.save()

        assigned_to_email = new_assigned_to_username.email

        task_instance = Task.objects.get(id=task.pk)
        serializer = TaskSerializer(
            task_instance, context={'request': request}
        )
        serialized_data = serializer.data

        serialized_data[
            'previous_assigned_to_username'] = previous_assigned_to_username

        template = (f'{TEMPLATES_DIR}/email_templates/'
                    f'reassigned_to_mail.html')

        send_email_message.apply_async(
            kwargs={
                'email': assigned_to_email,
                'template': template,
                'context': serialized_data,
            },
            countdown=5
        )

        return redirect('tracker:index')

    context = {
        'task': task,
        'form': form,
        'all_users': all_users
    }

    return render(request, 'tasks/create.html', context)


@login_required
def delete_task(request, pk):
    """Удаление задачи."""

    username = request.user
    task = get_object_or_404(Task, pk=pk)
    template = f'{TEMPLATES_DIR}/email_templates/delete_task_mail.html'

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
            'template': template,
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
