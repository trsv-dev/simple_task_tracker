from django.core.mail import send_mail
from django.template.loader import render_to_string

from task_tracker.settings import EMAIL_HOST_USER


def send_email_message(
        email,
        template,
        task=None,
        context_to_delete=None,
):
    """
    Отправка письма на электронную почту пользователю,
    которого отметили ответственным за выполнение задачи,
    письма о дедлайне, письма об удалении задачи.
    """

    if task:
        email_context = {
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

    if context_to_delete:
        message = render_to_string(template, context_to_delete)
    else:
        message = render_to_string(template, email_context)

    send_mail(
        'Письмо от Simple task tracker',
        message,
        EMAIL_HOST_USER,
        [email],
        html_message=message
    )
