import re
import socket
from datetime import timedelta
from smtplib import SMTPException
from urllib.parse import unquote_plus

from celery import shared_task
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone

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
