from threading import Thread

from django.core.mail import send_mail
from django.template.loader import render_to_string

from task_tracker.settings import EMAIL_HOST_USER


def send_email_message(email, template, task=None, context=None,):
    """
    Отправка письма на электронную почту пользователю,
    которого отметили ответственным за выполнение задачи,
    письма о дедлайне, письма об удалении задачи.
    """

    if task:
        create_context = {
            'author': task.author,
            'title': task.title,
            'description': task.description,
            'priority': task.priority,
            'status': task.status,
            'assigned_to': task.assigned_to,
            'created': task.created,
            'deadline': task.deadline,
            'is_done': task.is_done,
            'done_by': task.done_by if task.is_done else None,
            'done_by_time': task.done_by_time
        }

    if context:
        message = render_to_string(template, context)
    else:
        message = render_to_string(template, create_context)

    send_mail(
        subject='Письмо от Simple task tracker',
        message=message,
        from_email=EMAIL_HOST_USER,
        recipient_list=[email],
        html_message=message
    )


def send_email_message_async(email, template, task=None,
                             context=None):
    """
    Простая асинхронная отправка письма на электронную
    почту пользователю.
    """

    send_mail_thread = Thread(
        target=send_email_message,
        name='send_email_message',
        args=(email, template, task, context)
    )

    send_mail_thread.start()
