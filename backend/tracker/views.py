from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from tracker.forms import TaskCreateForm
from tracker.models import Task


def index(request):
    """Отображение главной страницы."""

    tasks = Task.objects.all()
    context = {'tasks': tasks}
    return render(request, 'base.html', context)


@login_required
def create_task(request):
    """Создание задачи."""

    username = request.user
    form = TaskCreateForm(request.POST)
    context = {'form': form}
    if form.is_valid():
        task = form.save(commit=False)
        task.author = username
        form.save()
        return redirect('tracker:index')
    return render(request, 'tasks/create.html', context)


@login_required
def edit_task(request, pk):
    """Редактирование задачи."""

    username = request.user
    task = get_object_or_404(Task, pk=pk)
    if not (username == task.author or username.is_staff):
        return redirect('tracker:index')
    form = TaskCreateForm(request.POST, instance=task)
    if form.is_valid():
        form.save()
        return redirect('tracker:index')
    context = {'task': task}
    return render(request, 'tasks/create.html', context)


@login_required
def delete_task(request, pk):
    """Удаление задачи."""

    username = request.user
    task = get_object_or_404(Task, pk=pk)
    if task.author != username:
        return redirect('tracker:index')
    task.delete()
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
