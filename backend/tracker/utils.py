import re
import socket
from datetime import timedelta
from smtplib import SMTPException

from celery import shared_task, current_task
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone

from task_tracker.settings import EMAIL_HOST_USER, TEMPLATES_DIR, BASE_URL
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


def notify_mentioned_users(request, comment_text, comment_task):
    """
    Если в комментарии пользователя указали через @username
    присылает уведомление на электронную почту об упоминании.
    """

    search_pattern = re.compile(r'@(\w+)')
    mentioned_usernames = search_pattern.findall(comment_text)

    task_instance = comment_task

    for username in mentioned_usernames:
        user = get_object_or_404(User, username=username)
        user_email = user.email

        # Получаем данные username из сериализатора, иначе Celery не пропустит
        # несериализованные данные.
        user_instance = user

        # serializer = UserSerializer(
        #     user_instance, context={'request': request}
        # )

        serializer = UserSerializer(user_instance)

        username = serializer.data['username']

        # Получаем данные комментария из сериализатора,
        # иначе Celery не пропустит несериализованные данные.

        # Раскомментировать если используем сериализатор из DRF.
        # serializer = TaskSerializer(
        #     task_instance, context={'request': request}
        # )

        serializer = TaskSerializer(task_instance)

        comment_task = serializer.data['title']
        task_link = serializer.data['link']

        comment_author = request.user.username

        context = {
            'username': username,
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
