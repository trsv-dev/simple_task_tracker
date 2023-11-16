import socket
from datetime import timedelta
from smtplib import SMTPException

from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from task_tracker.settings import EMAIL_HOST_USER, TEMPLATES_DIR, BASE_URL
from tracker.models import Task
from tracker.serializers import TaskSerializer


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
def send_email_about_closer_deadline():
    """
    Получение списка всех задач с подходящими дедлайнами
    и отправка электронных писем о них. Пометка задач с уже
    отправленными сообщениями о дедлайне. При изменении
    дедлайна в дальнейшем в процессе редактирования задачи
    отметка снимается.
    """

    tasks_with_closer_deadlines = Task.objects.filter(
        deadline__lt=timezone.now() + timedelta(hours=24)
    )

    for task in tasks_with_closer_deadlines:
        if not task.is_notified:
            assigned_to_email = task.assigned_to.email
            task_instance = task

            serializer = TaskSerializer(
                task_instance, context={'base_url': BASE_URL}
            )

            serialized_data = serializer.data

            send_email_message.apply_async(
                kwargs={
                    'email': assigned_to_email,
                    'template': f'{TEMPLATES_DIR}'
                                f'/email_templates/deadline_mail.html',
                    'context': serialized_data
                },
                countdown=5
            )
            task.is_notified = True
            task.save()
