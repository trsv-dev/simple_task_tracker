from copy import deepcopy
from datetime import datetime, timedelta
from urllib.parse import quote

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from task_tracker.settings import TASKS_IN_PAGE, DAYS_IN_CALENDAR_PAGE
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


def get_current_dates(dates, page_number, items_per_page):
    """Получаем список дат для текущей страницы. Используется для пагинации."""

    # Устанавливаем границы страниц.
    start_index = (page_number - 1) * items_per_page
    end_index = start_index + items_per_page

    # Получаем список дат для текущей страницы.
    current_dates = dates[start_index:end_index]

    return current_dates


def get_tasks_by_date(full_archive, current_dates, date_field: str):
    """
    Получаем словарь из дней и задач по дням для конкретной
    страницы пагинатора.
    """

    # Создаем словарь, где ключ - дата, значение - задачи,
    # выполненные в этот день.

    tasks_by_date = {}
    for date in current_dates:
        tasks_by_date[date[date_field]] = full_archive.filter(
            done_by_time__date=date[date_field]
        )

    return tasks_by_date


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

    # if not request.user.is_authenticated:
    #     return redirect('users:login')

    tasks = Task.objects.all()
    current_data = timezone.now()

    # Отображаем завершенные за сутки задания.
    delta = current_data - timedelta(hours=24)

    completed_tasks = tasks.filter(
        is_done=True,
        done_by_time__gte=delta,
        done_by_time__lte=current_data
    )

    context = {
        'tasks': tasks,
        'completed_tasks': completed_tasks
    }

    return render(request, 'base.html', context)


def profile(request, user):
    """Отображение профиля пользователя."""

    user_profile = get_object_or_404(User, username=user)
    context = {
        'user_profile': user_profile
    }

    return render(request, 'tasks/profile.html', context)


def current_tasks(request, user):
    """Отображение текущих задач пользователя."""

    profile_user = get_object_or_404(User, username=user)
    tasks = Task.objects.filter(
        assigned_to=profile_user, done_by=None
    ).order_by('deadline')

    paginator = Paginator(tasks, TASKS_IN_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'username': profile_user,
        'current_tasks_quantity': len(tasks),
        'page_obj': page_obj,
        'current_time': timezone.now()
    }

    return render(request, 'tasks/current_tasks.html', context)


def user_archive(request, user):
    """Архив выполненных задач пользователя."""

    if not request.user.is_authenticated:
        return redirect('users:login')

    profile_user = get_object_or_404(User, username=user)

    archived_tasks = Task.objects.filter(
        assigned_to=profile_user, done_by=profile_user
    ).order_by('-done_by_time__date')

    dates = archived_tasks.values('done_by_time__date').distinct()

    items_in_page = DAYS_IN_CALENDAR_PAGE
    page_number = int(request.GET.get('page', 1))

    current_dates = get_current_dates(dates, page_number, items_in_page)

    tasks_by_date = {}
    for date in current_dates:
        tasks_by_date[date['done_by_time__date']] = archived_tasks.filter(
            done_by_time__date=date['done_by_time__date']
        )

    paginator = Paginator(dates, items_in_page)
    page_obj = paginator.get_page(page_number)

    context = {
        'username': profile_user,
        'archived_tasks_quantity': len(archived_tasks),
        'tasks_by_date': tasks_by_date,
        'page_obj': page_obj
    }

    return render(request, 'tasks/user_archive.html', context)


def delegated_tasks(request, user):
    """Список задач, делегированных другим пользователям по дням."""

    if not request.user.is_authenticated:
        return redirect('users:login')

    tasks = Task.objects.all()
    username = get_object_or_404(User, username=user)
    delegated_tasks = tasks.filter(author=username)
    undone_delegated_tasks = tasks.filter(author=username, is_done=False)

    dates = delegated_tasks.values('created__date').order_by(
        '-created__date'
    ).distinct()

    items_per_page = DAYS_IN_CALENDAR_PAGE

    page_number = int(request.GET.get('page', 1))

    current_dates = get_current_dates(dates, page_number, items_per_page)

    tasks_by_date = {}
    for date in current_dates:

        tasks_by_date[date['created__date']] = delegated_tasks.filter(
            created__date=date['created__date']
        )

    paginator = Paginator(dates, items_per_page)
    page_obj = paginator.get_page(page_number)

    context = {
        'username': username,
        'delegated_tasks_quantity': len(delegated_tasks),
        'undone_delegated_tasks_quantity': len(undone_delegated_tasks),
        'tasks_by_date': tasks_by_date,
        'page_obj': page_obj,
        'current_time': timezone.now()
    }

    return render(request, 'tasks/delegated_tasks.html', context)


def get_undone_delegated_tasks(request, user):
    """Список невыполненных задач, делегированных другим пользователям."""

    if not request.user.is_authenticated:
        return redirect('users:login')

    username = get_object_or_404(User, username=user)

    undone_delegated_tasks = Task.objects.filter(
        author=username, is_done=False
    )

    order_by = request.GET.get('order_by', 'created')

    undone_delegated_tasks = undone_delegated_tasks.order_by(order_by)

    page_number = request.GET.get('page')
    paginator = Paginator(undone_delegated_tasks, TASKS_IN_PAGE)
    page_obj = paginator.get_page(page_number)

    context = {
        'username': username,
        'undone_delegated_tasks_quantity': len(undone_delegated_tasks),
        'order_by': order_by,
        'page_obj': page_obj,
        'current_time': timezone.now()
    }

    return render(
        request, 'tasks/undone_delegated_tasks.html', context
    )


def full_archive_by_dates(request):
    """Отображение всего архива выполненных задач по дням."""

    if not request.user.is_authenticated:
        return redirect('users:login')

    full_archive = Task.objects.filter(is_done=True)#.order_by('-done_by_time')

    dates = full_archive.values('done_by_time__date').order_by(
        '-done_by_time__date'
    ).distinct()

    items_per_page = DAYS_IN_CALENDAR_PAGE

    # Получаем номер текущей страницы из запроса пользователя.
    # При переходе с главной страницы request.GET.get('page')
    # возвращает 'None', поэтому подстраховываемся.

    page_number = int(request.GET.get('page', 1))

    # Получаем список дат для текущей страницы.
    current_dates = get_current_dates(dates, page_number, items_per_page)

    # Создаем словарь, где ключ - дата, значение - задачи,
    # выполненные в этот день.

    tasks_by_date = get_tasks_by_date(
        full_archive, current_dates, 'done_by_time__date'
    )

    # Создаем объект Paginator для навигации по страницам
    paginator = Paginator(dates, items_per_page)
    page_obj = paginator.get_page(page_number)

    context = {
        'full_archive_quantity': len(full_archive),
        'tasks_by_date': tasks_by_date,
        'page_obj': page_obj,
    }

    return render(request, 'tasks/full_archive.html', context)


def task_detail(request, pk):
    """Отображение деталей задачи."""

    task = get_object_or_404(Task, pk=pk)
    comments = Comment.objects.filter(task=task)
    form = CommentForm(request.POST)

    context = {
        'task': task,
        'comments': comments,
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
    email = task.author.email
    task.previous_status = task.status
    task.is_done = True
    task.status = 'Выполнено'
    task.done_by = username
    task.done_by_time = timezone.now()
    # Отменяем проверку даты и времени напоминания о дедлайне в модели.
    task.save(skip_deadline_reminder_check=True)

    universal_mail_sender(request, task, email,
                          templates['task_is_done_mail'])

    return redirect('tracker:index')


@login_required
def mark_as_undone(request, pk):
    """Пометить задание как невыполненное."""

    task = get_object_or_404(Task, pk=pk)
    email = task.author.email
    if task.is_done:
        task.is_done = False
        task.status, task.previous_status = task.previous_status, task.status
        task.done_by_time = None
        task.done_by = None
        # Отменяем проверку даты и времени напоминания о дедлайне в модели.
        task.save(skip_deadline_reminder_check=True)

        universal_mail_sender(request, task, email,
                              templates['task_is_undone_mail'])

        return redirect('tracker:index')


@login_required
def change_task_status(request, pk):
    """Изменение статуса задачи назначенным пользователем."""

    task = get_object_or_404(Task, pk=pk)
    username = request.user
    current_status = task.status

    if task.status == 'Ожидает выполнения' and task.assigned_to == username:
        task.status = 'В процессе выполнения'
        task.previous_status = current_status
        task.save(skip_deadline_reminder_check=True)

    elif (task.status == 'В процессе выполнения' and
          task.assigned_to == username):
        task.status = 'Ожидает выполнения'
        task.previous_status = current_status
        task.save(skip_deadline_reminder_check=True)

    return redirect('tracker:detail', pk=pk)


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
        # Экранируем символы с помощью quote, т.к. в комментах может быть код.
        # comment.text = quote(comment.text)
        form.save()

        notify_mentioned_users(request, quote(comment.text), comment.task)

        parent_id = request.POST.get('parent')
        if parent_id:
            parent = get_object_or_404(Comment, pk=parent_id)
            comment.parent = parent
            comment.save()

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
