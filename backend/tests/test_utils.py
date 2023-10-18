import threading

from django.contrib.auth import get_user_model
from django.core import mail
from django.http import HttpRequest
from django.test import TestCase
from django.utils import timezone

from task_tracker.settings import TEMPLATES_DIR
from tracker.models import Task
from tracker.utils import send_email_message, send_email_message_async
from tracker.views import get_task_link

User = get_user_model()


class EmailTestCase(TestCase):
    """Тестирование отправки электронной почты."""

    def setUp(self):
        """Тестовые данные."""

        self.test_user = User.objects.create_user(
            username='test_user',
            email='test_user@test.test'
        )
        self.test_assigned_to_user = User.objects.create_user(
            username='assigned_to_user',
            email='assigned_to_user@test.test'
        )

        self.test_data = {
            'author': self.test_user,
            'title': 'Тестовая задача',
            'description': 'Описание тестовой задачи',
            'priority': 'Высокий',
            'status': 'Ожидает выполнения',
            'previous_status': '',
            'assigned_to': self.test_user,
            'deadline': timezone.make_aware(
                timezone.datetime(2100, 1, 1)
            ),
            'is_done': 'False',
            'done_by': None,
            'done_by_time': None
        }

        self.test_task = Task.objects.create(**self.test_data)

        self.context_to_edit = {
            'previous_assigned_to_username': self.test_user,
            'assigned_to': self.test_assigned_to_user,
            'author': self.test_task.author.username,
            'title': self.test_task.title
        }

        self.context_to_delete = {
            'author': self.test_task.author.username,
            'title': self.test_task.title,
            'username': self.test_user.username,
            'assigned_to': self.test_task.assigned_to
        }

        self.fake_request = HttpRequest()
        self.fake_request.method = 'GET'
        self.fake_request.META = {
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '8000'
        }

    def tearDown(self):
        """Удаляем тестовые данные после прохождения тестов."""

        mail.outbox.clear()
        self.test_task.delete()
        self.test_user.delete()
        self.test_assigned_to_user.delete()

    def test_email_sending_with_task(self):
        """Тестируем простую отправку почты."""

        email_template = f'{TEMPLATES_DIR}/email_templates/task_mail.html'

        send_email_message(
            email=self.test_user.email,
            template=email_template,
            task=self.test_task,
            link=get_task_link(self.fake_request, pk=self.test_task.pk)
        )

        self.assertEqual(len(mail.outbox), 1)

        self.assertIn(
            self.test_task.title,
            mail.outbox[0].body,
            msg='Заголовка задачи нет в письме!'
        )

    def test_async_email_sending_with_task(self):
        """Тестируем асинхронную отправку почты."""

        email_template = f'{TEMPLATES_DIR}/email_templates/task_mail.html'

        send_email_message_async(
            email=self.test_user.email,
            template=email_template,
            task=self.test_task,
            link=get_task_link(self.fake_request, self.test_task.pk),
        )

        # Получаем первый поток (и подразумеваем, что он единственный,
        # т.к. вызов функции один), для этого берем срез.

        send_email_thread = [
            t for t in threading.enumerate() if t.name == 'send_email_message'
        ][0]

        send_email_thread.join(timeout=5)

        self.assertEqual(len(mail.outbox), 1)

        self.assertIn(
            self.test_task.title,
            mail.outbox[0].body,
            msg='Заголовка задачи нет в письме!'
        )

    def test_email_sending_with_edit_delete_context(self):
        """Тестируем отправку почты с контекстом."""

        email_templates = (
            f'{TEMPLATES_DIR}/email_templates/reassigned_to_mail.html',
            f'{TEMPLATES_DIR}/email_templates/delete_task_mail.html'
        )
        contexts = (self.context_to_edit, self.context_to_delete)

        for template, context in enumerate(contexts):
            send_email_message(
                email=self.test_assigned_to_user,
                template=email_templates[template],
                context=context
            )

        # Ожидаем, что количество отправленных писем равно 2
        self.assertEqual(len(mail.outbox), 2)

        self.assertTrue(
            mail.outbox[0].body != mail.outbox[1].body,
            msg='Тексты писем совпадают. Письма не должны '
                'содержать один и тот же текст!'
        )

    def test_async_email_sending_with_context(self):
        """Тестируем асинхронную отправку почты с контекстом."""

        email_templates = (
            f'{TEMPLATES_DIR}/email_templates/reassigned_to_mail.html',
            f'{TEMPLATES_DIR}/email_templates/delete_task_mail.html'
        )

        contexts = (self.context_to_edit, self.context_to_delete)

        for template, context in enumerate(contexts):
            send_email_message_async(
                email=self.test_assigned_to_user,
                template=email_templates[template],
                context=context
            )

        for thread in threading.enumerate():
            if thread.name == 'send_email_message':
                thread.join(timeout=5)

        # Ожидаем, что количество отправленных писем равно 2
        self.assertEqual(len(mail.outbox), 2)

        self.assertTrue(
            mail.outbox[0].body != mail.outbox[1].body,
            msg='Тексты писем совпадают. Письма не должны '
                'содержать один и тот же текст!'
        )
