from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404

from tags.models import Tags, TaskTag


def filter_by_tag(request, tag_name):

    tag = get_object_or_404(Tags, name=tag_name)

    tasks_by_tag = TaskTag.objects.filter(
        tag_id=tag.id).order_by(
        'task__created').prefetch_related('task__author')

    tasks = [task_by_tag.task for task_by_tag in tasks_by_tag]

    paginator = Paginator(tasks, settings.TASKS_IN_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'tag_name': tag.name,
        'page_obj': page_obj
    }

    return render(request, 'tags/by_tag.html', context)
