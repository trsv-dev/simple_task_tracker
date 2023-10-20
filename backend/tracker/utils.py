from threading import Thread

from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string

from task_tracker.settings import EMAIL_HOST_USER, TEMPLATES_DIR


@shared_task
def send_email_message(email, template, context):
    """
    Отправка письма на электронную почту пользователю,
    которого отметили ответственным за выполнение задачи,
    письма о дедлайне, письма об удалении задачи.
    """

    mail_context = {}

    mail_context.update(context)

    message = render_to_string(template, mail_context)

    send_mail(
        subject='Письмо от Simple task tracker',
        message=message,
        from_email=EMAIL_HOST_USER,
        recipient_list=[email],
        html_message=message
    )


@shared_task
def deadline_reminder_email(email, context):

    template = f'{TEMPLATES_DIR}/email_templates/deadline_mail.html'
    message = render_to_string(template, context)

    send_mail(
        subject='Письмо от Simple task tracker',
        message=message,
        from_email=EMAIL_HOST_USER,
        recipient_list=[email],
        html_message=message
    )
