from django.http import HttpResponse
from django.shortcuts import render, redirect

from tracker.models import Task
from tracker.forms import TaskCreateForm


def index(request):
    tasks = Task.objects.all()
    context = {'tasks': tasks}
    return render(request, 'base.html', context)


def create_task(request):
    form = TaskCreateForm(request.POST or None)
    if form.is_valid():
        task = form.save(commit=False)
        task.save()
        return redirect('index')
    else:
        form = TaskCreateForm()
    return render(request, 'tasks/create.html', {'form': form})
