from copy import deepcopy
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from favorites.models import Favorites
from images.views import handle_images
from tags.models import TaskTag
from tracker.forms import TaskCreateForm
from tracker.models import Task
from tracker.utils import (templates, universal_mail_sender,
                           get_common_context, catch_message,
                           get_page_obj)


def check_rights_to_task(username, task):
    """
    Проверяем, является ли пользователь автором задачи,
    админом или ответственным за задачу.
    """

    return (username == task.author or
            username.is_staff or
            username == task.assigned_to)


def get_current_dates(dates, page_number, items_per_page):
    """Получаем список дат для текущей страницы. Используется для пагинации."""

    # Устанавливаем границы страниц.
    start_index = (page_number - 1) * items_per_page
    end_index = start_index + items_per_page

    # Получаем список дат для текущей страницы.
    current_dates = dates[start_index:end_index]

    return current_dates


def get_tasks_by_date(queryset, current_dates,
                      date_field: str, attribute: str):
    """
    Получаем словарь из дней и задач по дням для конкретной
    страницы пагинатора.
    """

    # Создаем словарь, где ключ - дата, значение - задачи,
    # выполненные в этот день.

    tasks_by_date = {}
    for date in current_dates:
        tasks_by_date[date[date_field]] = [
            task for task in queryset
            if getattr(task, attribute).date() == date[date_field]
        ]

    return tasks_by_date


def check_deadline_or_deadline_reminder(new_deadline, new_deadline_reminder):
    """
    Проверка дедлайна и времени напоминания о дедлайне.
    Дедлайн не должен быть в прошлом.
    Напоминание о дедлайне не должно быть в прошлом.
    Напоминание о дедлайне не должно быть позже дедлайна.
    """

    return (new_deadline > timezone.now() and
            new_deadline_reminder > timezone.now() and
            new_deadline_reminder < new_deadline)


def is_title_description_priority_status_changed(request, original_task, form):
    """
    Проверяем что изменения есть только в заголовке, описании,
    приоритете и статусе. Если заголовок, приоритет, статус, описание, картинки
    отличаются от начальных, а уведомление уже приходило или дата уведомления
    валидна и пользователь не менялся - возвращаем True.
    """

    form_data = form.cleaned_data

    return (((form_data.get('status') != original_task.status or
              form_data.get('priority') != original_task.priority) or
             (form_data.get('title') != original_task.title or
              form_data.get('description') != original_task.description) or
             request.FILES.getlist('image')) and
            (original_task.is_notified or
             form_data.get('deadline') >
             form_data.get('deadline_reminder') >
             timezone.now())
            and form_data.get(
                'assigned_to').username == original_task.assigned_to.username)


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
        if not original_task.is_draft:
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

        if not original_task.is_draft:
            universal_mail_sender(
                request,
                task,
                assigned_to_email,
                templates['reassigned_task_template'],
                priority=0,
                queue='fast_queue',
                previous_assigned_to_username=original_task.assigned_to.username
            )


@transaction.atomic
def save_transaction(request, form, object=None, model=None,
                     skip_deadline_reminder_check=None):
    """Транзакция сохранения задачи или комментария и обработки изображений."""

    if 'delete_image' in request.POST:
        object.images.all().delete()

    if skip_deadline_reminder_check:
        handle_images(request, object, model)
        object.save(skip_deadline_reminder_check=True)
    else:
        form.save()
        handle_images(request, object, model)


def save_obj_and_handle_form_errors(request, form, all_users=None,
                                    object=None,
                                    model=None,
                                    skip_deadline_reminder_check=None):
    """
    Попытка сохранить задачу и вывод ошибок для дальнейшего
    отображения в форме при неудачном сохранении.
    """

    try:
        if skip_deadline_reminder_check:
            save_transaction(request, form, object, model,
                             skip_deadline_reminder_check)

        else:
            save_transaction(request, form, object, model,
                             skip_deadline_reminder_check=None)

        return None
    except ValidationError as e:
        form.add_error(None, e)
        if object:
            context = {
                'task_form': form,
                'all_users': all_users
            }
        else:
            context = {
                'task': object,
                'task_form': form,
                'all_users': all_users
            }
        return context


def index(request):
    """Отображение главной страницы."""

    # if not request.user.is_authenticated:
    #     return redirect('users:login')

    catch_message(request)

    tasks = Task.objects.select_related('author', 'assigned_to').all()

    # pending = tasks.filter(status='Ожидает выполнения')
    # in_progress = tasks.filter(status='В процессе выполнения')

    # Уменьшаем на 1 кол-во запросов к БД
    tasks = tasks.filter(
        status__in=['Ожидает выполнения', 'В процессе выполнения',
                    'Выполнено'], is_draft=False
    )
    pending = [task for task in tasks if task.status == 'Ожидает выполнения']
    in_progress = [
        task for task in tasks if task.status == 'В процессе выполнения'
    ]

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
        'pending': pending,
        'in_progress': in_progress,
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
        assigned_to=profile_user, done_by=None, is_draft=False
    ).order_by('deadline').select_related('author', 'assigned_to')

    page_obj = get_page_obj(request, tasks, settings.TASKS_IN_PAGE)

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
        assigned_to=profile_user, done_by=profile_user, is_draft=False
    ).order_by('-done_by_time__date').select_related('author', 'assigned_to')

    dates = archived_tasks.values('done_by_time__date').distinct()

    items_in_page = settings.DAYS_IN_CALENDAR_PAGE
    page_number = int(request.GET.get('page', 1))

    current_dates = get_current_dates(dates, page_number, items_in_page)

    tasks_by_date = get_tasks_by_date(
        archived_tasks, current_dates,
        'done_by_time__date', 'done_by_time'
    )

    page_obj = get_page_obj(
        request, dates, settings.DAYS_IN_CALENDAR_PAGE
    )

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

    username = get_object_or_404(User, username=user)
    delegated_tasks = Task.objects.filter(
        author=username, is_draft=False).select_related('author', 'assigned_to')
    undone_delegated_tasks = delegated_tasks.filter(
        author=username, is_done=False).select_related('author', 'assigned_to')

    dates = delegated_tasks.select_related(
        'author').values('created__date').order_by('-created__date').distinct()

    items_per_page = settings.DAYS_IN_CALENDAR_PAGE

    page_number = int(request.GET.get('page', 1))

    current_dates = get_current_dates(dates, page_number, items_per_page)

    tasks_by_date = get_tasks_by_date(
        delegated_tasks, current_dates,
        'created__date', 'created'
    )

    page_obj = get_page_obj(
        request, dates, settings.DAYS_IN_CALENDAR_PAGE
    )

    context = {
        'username': username,
        'delegated_tasks_quantity': len(delegated_tasks),
        'undone_delegated_tasks_quantity': len(undone_delegated_tasks),
        'tasks_by_date': tasks_by_date,
        'page_obj': page_obj,
        'current_time': timezone.now(),
        'search_query': request.GET.get('query', '')
    }

    return render(request, 'tasks/delegated_tasks.html', context)


def get_undone_delegated_tasks(request, user):
    """Список невыполненных задач, делегированных другим пользователям."""

    if not request.user.is_authenticated:
        return redirect('users:login')

    username = get_object_or_404(User, username=user)

    undone_delegated_tasks = Task.objects.filter(
        author=username, is_done=False, is_draft=False
    ).select_related('author', 'assigned_to')

    order_by = request.GET.get('order_by', 'created')

    undone_delegated_tasks = undone_delegated_tasks.order_by(order_by)

    page_obj = get_page_obj(
        request, undone_delegated_tasks, settings.TASKS_IN_PAGE
    )

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

    full_archive = Task.objects.filter(
        is_done=True, is_draft=False).select_related('author', 'assigned_to')

    dates = full_archive.values('done_by_time__date').order_by(
        '-done_by_time__date'
    ).distinct()

    items_per_page = settings.DAYS_IN_CALENDAR_PAGE

    # Получаем номер текущей страницы из запроса пользователя.
    # При переходе с главной страницы request.GET.get('page')
    # возвращает 'None', поэтому подстраховываемся.

    page_number = int(request.GET.get('page', 1))

    # Получаем список дат для текущей страницы.
    current_dates = get_current_dates(dates, page_number, items_per_page)

    # Создаем словарь, где ключ - дата, значение - задачи,
    # выполненные в этот день.

    tasks_by_date = get_tasks_by_date(
        full_archive, current_dates,
        'done_by_time__date', 'done_by_time'
    )

    # Создаем объект Paginator для навигации по страницам
    page_obj = get_page_obj(
        request, dates, settings.DAYS_IN_CALENDAR_PAGE
    )

    context = {
        'full_archive_quantity': len(full_archive),
        'tasks_by_date': tasks_by_date,
        'page_obj': page_obj,
    }

    return render(request, 'tasks/full_archive.html', context)


def drafts(request, user):
    """Черновики пользователя (неопубликованные задачи)."""

    user = get_object_or_404(User, username=user)

    if not user.is_authenticated:
        return redirect('users:login')

    drafts = Task.objects.filter(
        author=user, is_draft=True).select_related('author', 'assigned_to')

    dates = drafts.select_related(
        'author').values('created__date').order_by('-created__date').distinct()

    items_per_page = settings.DAYS_IN_CALENDAR_PAGE
    page_number = int(request.GET.get('page', 1))
    current_dates = get_current_dates(dates, page_number, items_per_page)

    tasks_by_date = get_tasks_by_date(
        drafts, current_dates,
        'created__date', 'created'
    )

    # Создаем объект Paginator для навигации по страницам
    page_obj = get_page_obj(
        request, dates, settings.DAYS_IN_CALENDAR_PAGE
    )

    context = {
        'username': user,
        'drafts_quantity': len(drafts),
        'tasks_by_date': tasks_by_date,
        'page_obj': page_obj,
    }

    return render(request, 'tasks/drafts.html', context)


def task_detail(request, pk):
    """Отображение деталей задачи."""

    catch_message(request)

    task = get_object_or_404(
        Task.objects.select_related('author', 'assigned_to', 'done_by')
        .prefetch_related('tags__tag'), pk=pk)

    comments = task.comments.select_related('author').prefetch_related(
        'images', 'author__profile').annotate(likes_count=Count('likes'))

    context = get_common_context(request, task, comments)

    context['in_favorites'] = Favorites.objects.filter(task=task).values(
        'user').count()

    if request.user.is_authenticated:
        users_likes = request.user.likes.select_related(
            'user').prefetch_related('comment')

        # users_likes_dict = {}
        # for likes in users_likes:
        #     users_likes_dict[likes.comment.text] = likes.user.username

        # Передаем в словарь pk лайкнутых пользователем сообщений,
        # чтобы потом в шаблоне его "разобрать" и отметить значком "+1"
        # сообщение, если оно было лайкнуто
        users_likes_dict = {}
        for likes in users_likes:
            users_likes_dict[likes.comment.pk] = likes.user.username

        context['users_likes_dict'] = users_likes_dict

    return render(request, 'tasks/task_detail.html', context)


@login_required
def create_task(request):
    """Создание задачи."""

    username = request.user
    all_users = User.objects.all()
    form = TaskCreateForm(request.POST or None, request.FILES or None)
    deadline_reminder_str = request.POST.get('deadline_reminder')

    context = {
        'form': form,
        'current_user': username,
        'all_users': all_users,
    }

    if form.is_valid():
        task = form.save(commit=False)
        task.author = username
        tags = form.cleaned_data.get('tags', [])

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

        # Т.к. task уже есть (task = form.save(commit=False)) то передаем
        # форму, чтобы попытаться ее сохранить и task, с которым мы свяжем
        # изображения в случае успешного сохранения form.
        result = save_obj_and_handle_form_errors(request, form,
                                                 all_users, task, Task)

        if result:
            context.update(result)
            return render(request, 'tasks/create.html', context)

        task_tags = [TaskTag(task=task, tag=tag) for tag in tags]
        # Создаем объекты TaskTag одним запросом.
        TaskTag.objects.bulk_create(task_tags)

        assigned_to_email = task.assigned_to.email

        if not task.is_draft:
            universal_mail_sender(request, task, assigned_to_email,
                                  templates['create_task_template'])

        url = settings.BASE_URL + reverse('tracker:detail', args=[task.pk])
        messages.success(
            request, f'<a href="{url}">Задача</a> успешно создана!'
        )

        return redirect('tracker:index')
    return render(request, 'tasks/create.html', context)


@login_required
@transaction.atomic
def edit_task(request, pk):
    """Редактирование задачи."""

    username = request.user
    all_users = User.objects.all()
    # all_users = User.objects.prefetch_related('tasks').all()
    task = get_object_or_404(
        Task.objects
        .select_related('author', 'assigned_to')
        .prefetch_related('images'),
        pk=pk
    )

    existing_tags = task.tags.select_related('task').prefetch_related('tag')
    initial_tags = [tasktag.tag.name for tasktag in existing_tags]

    original_task = deepcopy(task)

    if not check_rights_to_task(username, task):
        return redirect('tracker:index')

    form = TaskCreateForm(
        request.POST or None, request.FILES or None, instance=task
    )

    context = {
        'task': task,
        'initial_tags': initial_tags,
        'form': form,
        'all_users': all_users,

    }

    if form.is_valid():
        task = form.save(commit=False)
        new_assigned_to = form.cleaned_data.get('assigned_to')
        new_deadline = form.cleaned_data.get('deadline')
        new_deadline_reminder = form.cleaned_data.get('deadline_reminder')
        tags = form.cleaned_data.get('tags', [])

        # Если оригинальное задание было черновиком и с него сняли
        # отметку черновика - отправляем письмо о новом задании
        # ответственному пользователю.
        if original_task.is_draft and not task.is_draft:
            universal_mail_sender(request, task, task.assigned_to.email,
                                  templates['create_task_template'])

            messages.warning(request, 'Черновик переведен в статус задачи!')

        if is_title_description_priority_status_changed(request,
                                                        original_task, form):

            skip_deadline_reminder_check = True
            result = save_obj_and_handle_form_errors(
                request, form, all_users,
                task, Task, skip_deadline_reminder_check
            )

            if result:
                context.update(result)

                return render(request, 'tasks/create.html', context)

            messages.warning(request, 'Изменения в задаче были сохранены!')
            return redirect('tracker:detail', pk=task.id)

        else:
            is_deadline_deadline_reminder_user_changed(request, original_task,
                                                       task, new_deadline,
                                                       new_deadline_reminder,
                                                       new_assigned_to)

            result = save_obj_and_handle_form_errors(request, form,
                                                     all_users, task, Task)

            if result:
                context.update(result)
                return render(request, 'tasks/create.html', context)

            task.tags.all().delete()
            task_tags = [TaskTag(task=task, tag=tag) for tag in tags]
            # Создаем объекты TaskTag одним запросом.
            TaskTag.objects.bulk_create(task_tags)

            messages.warning(request, 'Изменения в задаче были сохранены!')
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

    if not saved_task_data.is_draft:
        universal_mail_sender(request, saved_task_data, assigned_to_email,
                              templates['delete_task_template'])

    messages.info(request, f'Задача "{saved_task_data.title}" была удалена!')

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

    if not task.is_draft:
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

        if not task.is_draft:
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


def task_search(request):
    """Поиск по задачам."""

    # Не делал форму поиска, т.к. с формой поиска не смог добиться нужного
    # внешнего вида поля поиска в шаблоне. Обошелся прямым запросом из
    # шаблона к вьюхе.
    search_query = request.GET.get('query', '')

    if not search_query:
        context = {'no_results_message': 'Пустой поиск'}

        return render(request, 'tasks/task_search.html', context)

    search_results = Task.objects.filter(
        Q(title__icontains=search_query, is_draft=False) |
        Q(description__icontains=search_query, is_draft=False)
    ).order_by('title').select_related('author')

    page_obj = get_page_obj(
        request, search_results, settings.TASKS_IN_PAGE
    )

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'search_results': search_results
    }

    return render(request, 'tasks/task_search.html', context)
