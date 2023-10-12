from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from task_tracker.settings import TEMPLATES_DIR
from tracker.forms import TaskCreateForm
from tracker.models import Task
from tracker.utils import send_email_message_async


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
        'all_users': all_users
    }

    if form.is_valid():
        task = form.save(commit=False)
        task.author = username
        form.save()

        send_email_message_async(
            email=task.assigned_to.email,
            template=template,
            task=task,
        )

        return redirect('tracker:index')
    return render(request, 'tasks/create.html', context)


@login_required
def edit_task(request, pk):
    """Редактирование задачи."""

    username = request.user
    all_users = User.objects.all()
    task = get_object_or_404(Task, pk=pk)
    previous_assigned_to_username = task.assigned_to

    if check_rights_to_task(username, task) is False:
        return redirect('tracker:index')

    form = TaskCreateForm(request.POST, instance=task)

    if form.is_valid():
        task = form.save(commit=False)
        new_assigned_to_username = form.cleaned_data.get('assigned_to')

        if new_assigned_to_username != previous_assigned_to_username:
            task.assigned_to = new_assigned_to_username

            email = new_assigned_to_username.email

            template = (f'{TEMPLATES_DIR}/email_templates/'
                        f'reassigned_to_mail.html')

            context_to_edit = {
                'previous_assigned_to_username': previous_assigned_to_username,
                'assigned_to': task.assigned_to,
                'author': task.author.username,
                'title': task.title
            }

            send_email_message_async(
                email=email,
                template=template,
                context=context_to_edit
            )

        form.save()

        return redirect('tracker:index')

    context = {
        'task': task,
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

    email = task.assigned_to.email

    context_to_delete = {
        'author': task.author.username,
        'title': task.title,
        'username': username,
        'assigned_to':  task.assigned_to
    }

    task.delete()

    send_email_message_async(
        email=email,
        template=template,
        context=context_to_delete
    )

    return redirect('tracker:index')


@login_required
def mark_as_done(request, pk):
    """Пометить задачу как выполненную."""

    username = request.user
    task = Task.objects.get(pk=pk)
    task.is_done = True
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
        task.done_by_time = None
        task.done_by = None
        task.save()
        return redirect('tracker:index')
