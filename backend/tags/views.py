from django.conf import settings
from django.shortcuts import render, get_object_or_404

from tags.models import Tags, TaskTag
from tracker.utils import get_page_obj


def filter_by_tag(request, tag_name):
    """Отображение заданий, отмеченных определенным тегом."""

    tag = get_object_or_404(Tags, name=tag_name)

    tasks_by_tag = TaskTag.objects.filter(
        tag_id=tag.id,
        task__is_draft=False
    ).order_by('task__created').select_related(
        'task__assigned_to').prefetch_related('task__author')

    tasks = [task_by_tag.task for task_by_tag in tasks_by_tag]

    page_obj = get_page_obj(request, tasks, settings.TASKS_IN_PAGE)

    context = {
        'tag_name': tag.name,
        'page_obj': page_obj
    }

    return render(request, 'tags/by_tag.html', context)
