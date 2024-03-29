import asyncio
import re
import socket
from datetime import timedelta
from smtplib import SMTPException
from urllib.parse import unquote_plus

from celery import shared_task
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from bot.sending_messages import send_telegram_notification
from comments.forms import CommentForm
from task_tracker.settings import EMAIL_HOST_USER, TEMPLATES_DIR
from tracker.models import Task, User
from tracker.serializers import TaskSerializer, UserSerializer

templates = {
    'create_task_template':
        f'{TEMPLATES_DIR}/email_templates/task_mail.html',
    'delete_task_template':
        f'{TEMPLATES_DIR}/email_templates/delete_task_mail.html',
    'reassigned_task_template':
        f'{TEMPLATES_DIR}/email_templates/reassigned_to_mail.html',
    'deadline_template':
        f'{TEMPLATES_DIR}/email_templates/deadline_mail.html',
    'new_deadline_template':
        f'{TEMPLATES_DIR}/email_templates/new_deadline_mail.html',
    'message_to_mentioned_user':
        f'{TEMPLATES_DIR}/email_templates/message_to_mentioned_user.html',
    'task_is_done_mail':
        f'{TEMPLATES_DIR}/email_templates/task_is_done_mail.html',
    'task_is_undone_mail':
        f'{TEMPLATES_DIR}/email_templates/task_is_undone_mail.html'
}


def get_chat_id(user):
    """Возвращает chat_id пользователя для отправки сообщения в Telegram."""

    user = get_object_or_404(User, username=user.username)

    return user.profile.telegram_chat_id if (
        user.profile.notify_in_telegram) else False


def send_to_telegram(task, user, message_type: str):
    """Отправка сообщения о событии в Telegram."""

    chat_id = get_chat_id(user)
    if chat_id and settings.TELEGRAM_TOKEN:
        asyncio.run(
            send_telegram_notification(task=task,
                                       chat_id=chat_id,
                                       message_type=message_type))


@shared_task(
    bind=True, autoretry_for=(socket.gaierror, SMTPException),
    retry_backoff=True, retry_kwargs={'max_retries': 30}
)
def send_email_message(self, email, template, context):
    """
    Отправка письма на электронную почту пользователю,
    которого отметили ответственным за выполнение задачи,
    письма о дедлайне, письма об удалении задачи, письма об
    упоминании в комментарии.
    """

    message = render_to_string(template, context)

    try:
        send_mail(
            subject='Письмо от Simple task tracker',
            message=message,
            from_email=EMAIL_HOST_USER,
            recipient_list=[email],
            html_message=message
        )
    except socket.gaierror as e:
        print(f'Временный сбой в разрешении имени: {e}')
        raise
    except SMTPException as e:
        print(f'Ошибка SMTP: {e}')
        raise


@shared_task
def send_email_about_closer_deadline(priority=9, queue='slow_queue'):
    """
    Получение списка всех задач с подходящими дедлайнами
    и отправка электронных писем о них. Пометка задач с уже
    отправленными сообщениями о дедлайне. При изменении
    дедлайна в дальнейшем в процессе редактирования задачи
    отметка снимается. Если задание выполнено до наступления времени
    напоминания - письмо не отправляется.
    """

    tasks_with_closer_deadlines = Task.objects.filter(
        deadline_reminder__lte=timezone.now() + timedelta(minutes=1),
        is_draft=False,
        is_done=False,
        is_notified=False
    )

    for task in tasks_with_closer_deadlines:
        if not task.is_notified:
            assigned_to_email = task.assigned_to.email
            task_instance = task

            # Раскомментировать если используем сериализатор из DRF.

            # serializer = TaskSerializer(
            #     task_instance, context={'base_url': BASE_URL}
            # )

            serializer = TaskSerializer(task_instance)

            serialized_data = serializer.data

            send_email_message.apply_async(
                kwargs={
                    'email': assigned_to_email,
                    'template': f'{TEMPLATES_DIR}'
                                f'/email_templates/deadline_mail.html',
                    'context': serialized_data
                },
                countdown=5,
                priority=priority,
                queue=queue
            )
            task.is_notified = True

            send_to_telegram(task, task.assigned_to, 'deadline')

            # На случай, если письмо "задержалось" из-за каких-либо причин
            # и deadline_reminder уже неактуален, установим
            # skip_deadline_reminder_check=True чтобы не было ошибки валидации,
            # а напоминание хоть и с опозданием, но пришло.

            task.save(skip_deadline_reminder_check=True)


def search_mentioned_users(comment_text, all_usernames_list):
    """Поиск в тексте комментария упомянутых через '@' пользователей."""

    comment_text = unquote_plus(comment_text)
    # Создаем множество пользователей сервера
    # all_usernames_list = set([user.username for user in User.objects.all()])
    # Регулярное выражение для поиска всех пользователей, упомянутых после '@'
    username_search_pattern = re.compile(r'@(\w+)')

    # Находим все совпадения (чтобы отследить упоминания в верхнем регистре
    # текст переводим в нижний регистр)
    matches = username_search_pattern.finditer(comment_text.lower())
    # Делаем из них список
    mentioned_usernames = [match.group(1) for match in matches]
    # Получаем множество найденных в тексте упоминаний
    mentioned_usernames_set = set(mentioned_usernames)
    all_usernames_set = set(all_usernames_list)
    # Находим и возвращаем пересечение множеств списка пользователей сервера и
    # найденных в тексте пользователей, упомянутых через '@' и
    # сущностей, в которых используется '@' (например, декораторы).
    # Получаем список отфильтрованных таким образом пользователей.

    return list(all_usernames_set & mentioned_usernames_set)


def notify_mentioned_users(request, comment_text, highlighted_comment_id,
                           list_of_mentioned_users, comment_task):
    """
    Если в комментарии пользователя указали через @username
    присылает уведомление на электронную почту об упоминании.
    """

    comment_text = unquote_plus(comment_text)
    task_instance = comment_task

    for username in list_of_mentioned_users:
        user = get_object_or_404(User, username=username)
        user_email = user.email

        # Получаем данные username из сериализатора, иначе Celery не пропустит
        # несериализованные данные.
        user_instance = user
        serializer = UserSerializer(user_instance)

        username = serializer.data['username']

        # Получаем данные комментария из сериализатора,
        # иначе Celery не пропустит несериализованные данные.

        serializer = TaskSerializer(task_instance)

        comment_task = serializer.data['title']
        task_link = serializer.data['link']

        comment_author = request.user.username

        context = {
            'username': username,
            'highlighted_comment_id': highlighted_comment_id,
            'comment_text': comment_text,
            'comment_task': comment_task,
            'comment_author': comment_author,
            'task_link': task_link
        }

        send_email_message.apply_async(
            kwargs={
                'email': user_email,
                'template': templates['message_to_mentioned_user'],
                'context': context
            },
            priority=9,
            queue='slow_queue',
            countdown=5
        )


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


def get_profile(username):
    """Получение ссылки на профиль пользователя."""

    return reverse('tracker:profile', kwargs={'user': username})


def get_all_usernames_list():
    """Получение юзернеймов всех пользователей."""

    return [user.username for user in User.objects.all()]


def get_common_context(request, task, comments):
    """
    Получение общего контекста для страницы деталей задачи,
    т.к. там отображаются детали задачи, комментарии и редактирование
    комментариев, которые имеют плюс/минус один контекст.
    """

    user = request.user
    comment_form = CommentForm(request.POST or None)
    comment_texts = [comment.text for comment in comments]
    comments_with_expired_editing_time = []
    images_in_task = task.images.all()

    # cache_name = 'images_cache'
    # images = cache.get('images_in_task')
    #
    # if images:
    #     images_in_task = images
    # else:
    #     images_in_task = task.images.all()
    #     cache.get(cache_name, images_in_task, 200)

    # Если пользователь аутентифицирован, то показываем кнопку добавления
    # в избранное
    if user.is_authenticated:
        is_favorited = bool(user.favorites.filter(task=task))
    images_in_comments = [comment.images.all() for comment in comments]

    highlighted_comment_id = int(request.GET.get('highlighted_comment_id', 0))

    for comment in comments:
        if timezone.now() > (comment.created + timedelta(minutes=30)):
            comments_with_expired_editing_time.append(comment)

    all_usernames_list = get_all_usernames_list()
    # Из списка списков делаем плоский список пользователей.
    list_of_mentioned_users = sum([search_mentioned_users(
        comment_text, all_usernames_list
    ) for comment_text in comment_texts], [])
    # Создаем словарь: ключ - имя пользователя, значение - ссылка на профиль.
    usernames_profiles_links = {
        username: get_profile(username) for username in list_of_mentioned_users
    }

    context = {
        'comment_form': comment_form,
        'task': task,
        'comments': comments,
        'comments_with_expired_editing_time':
            comments_with_expired_editing_time,
        'usernames_profiles_links': usernames_profiles_links,
        'images_in_task': images_in_task,
        # 'images_in_task': images,
        'images_in_comments': images_in_comments,
        'highlighted_comment_id': highlighted_comment_id
    }

    if not user.is_authenticated:
        return context

    # Если пользователь аутентифицирован, то показываем кнопку добавления
    # в избранное
    context['is_favorited'] = is_favorited
    return context


def catch_message(request):
    """Перехват информационных сообщений для отображения в интерфейсе."""

    message = request.GET.get('message')
    message_level = request.GET.get('message_level', 'success')

    if message:
        message_method = getattr(messages, message_level, messages.success)
        return message_method(request, message)


def get_page_obj(request, object, items_per_page):
    """Пагинатор. Возвращает page_obj."""

    paginator = Paginator(object, items_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj
