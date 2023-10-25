from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse

from task_tracker.settings import EMAIL_HOST_USER


def get_link(instance, request):
    """Получение прямой ссылки на задачу."""

    task_pk = instance.id

    return request.build_absolute_uri(
        reverse('tracker:detail', args=[task_pk])
    )


@shared_task
def send_email_message(email, template, context):
    """
    Отправка письма на электронную почту пользователю,
    которого отметили ответственным за выполнение задачи,
    письма о дедлайне, письма об удалении задачи.
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
    except Exception as e:
        print(f'Ошибка отправки почты: {e}')
