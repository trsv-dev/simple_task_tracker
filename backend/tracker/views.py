from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from tracker.forms import TaskCreateForm
from tracker.models import Task


def index(request):
    tasks = Task.objects.all()
    context = {'tasks': tasks}
    return render(request, 'base.html', context)


@login_required
def create_task(request):
    username = request.user
    form = TaskCreateForm(request.POST)
    context = {'form': form}
    if form.is_valid():
        task = form.save(commit=False)
        task.author = username
        form.save()
        return redirect('index')
    return render(request, 'tasks/create.html', context)


@login_required
def edit_task(request, pk):
    username = request.user
    task = get_object_or_404(Task, pk=pk)
    if not (username == task.author or username.is_staff):
        return redirect('index')
    form = TaskCreateForm(request.POST, instance=task)
    if form.is_valid():
        form.save()
        return redirect('index')
    context = {'task': task}
    return render(request, 'tasks/create.html', context)


@login_required
def delete_task(request, pk):
    username = request.user
    task = get_object_or_404(Task, pk=pk)
    if task.author != username:
        return redirect('index')
    task.delete()
    return redirect('index')
