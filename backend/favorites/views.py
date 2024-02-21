from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect

from favorites.models import Favorites
from tracker.models import Task, User
from tracker.views import get_current_dates, get_tasks_by_date


def add_to_favorites(request, pk):
    """Добавление задачи в избранное."""

    user = request.user
    task = get_object_or_404(Task, pk=pk)

    if not user.is_authenticated:
        return redirect('users:login')

    if user is not task.author:
        Favorites.objects.create(task=task, user=user)
        return redirect('tracker:detail', pk=task.pk)


def delete_from_favorites(request, pk):
    """Удаление задачи из избранного."""

    task = get_object_or_404(Task, pk=pk)
    user = request.user

    if not user.is_authenticated:
        return redirect('users:login')

    favorited_task = Favorites.objects.filter(task=task)
    favorited_task.delete()

    return redirect('tracker:detail', pk=task.pk)


def get_favorites(request, user):
    """Отображение избранного."""

    username = get_object_or_404(User, username=user)
    user_favorites = Favorites.objects.filter(
        user=username
    ).select_related('task__author')

    dates = user_favorites.order_by(
        'added_time__date'
    ).values('added_time__date').distinct()

    items_in_page = settings.DAYS_IN_CALENDAR_PAGE
    page_number = int(request.GET.get('page', 1))
    current_dates = get_current_dates(dates, page_number, items_in_page)

    tasks_by_date = get_tasks_by_date(
        user_favorites, current_dates,
        'added_time__date', 'added_time'
    )

    paginator = Paginator(dates, items_in_page)
    page_obj = paginator.get_page(page_number)

    context = {
        'username': username,
        'tasks_by_date': tasks_by_date,
        'page_obj': page_obj,
    }

    return render(request, 'favorites/favorites.html', context)
