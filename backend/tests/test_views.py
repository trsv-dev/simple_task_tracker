from http import HTTPStatus

from django.contrib.auth import get_user_model
# from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase, Client
from django.urls import reverse

from tracker.models import Task

User = get_user_model()


class ViewsTestCase(TestCase):
    """Тестируем вьюхи."""

    def setUp(self):
        """Тестовые данные."""

        self.test_user = User.objects.create_user(
            username='test_user'
        )
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.test_user)
        self.test_title = 'Тестовая задача'
        self.test_description = 'Описание тестовой задачи'
        self.test_data = {
            'author': self.test_user.id,
            'title': self.test_title,
            'description': self.test_description,
            'priority': 'Высокий',
            'status': 'В процессе выполнения',
            'deadline': '2100-01-01 00:00:00',
        }

    def tearDown(self):
        """Удаляем тестовые данные после прохождения тестов."""

        self.client.logout()
        self.test_user.delete()

    def test_homepage_by_guest_client(self):
        """Тестируем доступность главной страницы."""

        response = self.guest_client.get(reverse('index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_page_by_authorized_client(self):
        """
        Тестируем доступность страницы создания задачи
        для авторизованного пользователя.
        """

        response = self.authorized_client.get(reverse('create'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_task(self):
        """
        Тестируем простое создание задачи от заданного
        существующего пользователя.
        """

        response = self.authorized_client.post(
            reverse('create'),
            data=self.test_data
        )
        created_test_task = Task.objects.last()
        self.assertTrue(
            created_test_task,
            'Ошибка при создании объекта Task!'
        )
        self.assertTrue(
            Task.objects.filter(
                title='Тестовая задача',
                author=self.test_user
            ).exists()
        )

    def test_create_task_by_unauthorized_user(self):
        """
        Тестируем создание задачи от имени
        неавторизованного пользователя.
        """

        unauthorized_user = Client()
        response = unauthorized_user.post(
            reverse('create'),
            data=self.test_data,
        )

        self.assertFalse(
            Task.objects.filter(
                title=self.test_title,
                description=self.test_description
            ),
            msg='Задача не должна создаваться неавторизованным пользователем!'  # вынести в новый тест
        )

        self.assertIn(
            response.status_code,
            [HTTPStatus.FOUND, HTTPStatus.FORBIDDEN],
            'Неавторизованный пользователь должен быть переадресован!'
        )

    def test_delete_task_by_author(self):
        """Тестируем удаление задачи от существующего пользователя."""

        test_task = Task.objects.create(
            author=self.test_user,
            title=self.test_title,
            description=self.test_description
        )

        delete_url = reverse('delete', args=[test_task.pk])
        response = self.authorized_client.delete(delete_url)

        with self.assertRaises(ObjectDoesNotExist):
            Task.objects.get(pk=test_task.pk)

        self.assertEqual(
            response.status_code,
            HTTPStatus.FOUND,
            'Если пользователь не является автором должен '
            'происходить редирект на главную страницу!'
        )

    def test_delete_task_by_other_user(self):
        """
        Проверка удаления задачи от имени пользователя,
        отличного от автора задачи.
        """

        test_task = Task.objects.create(
            author=self.test_user,
            title=self.test_title,
            description=self.test_description
        )
        other_user = User.objects.create_user(username='other_user')
        other_client = Client()
        other_client.force_login(other_user)
        delete_url = reverse('delete', args=[test_task.pk])

        response = other_client.delete(delete_url)

        self.assertEqual(
            response.status_code,
            HTTPStatus.FOUND,
            'При попытке удаления задачи не автором должен '
            'происходить редирект на главную страницу (временно).'
        )

    def test_task_delete_response_status(self):
        """Тестируем статус ответа при удалении задачи."""

        test_task = Task.objects.create(
            author=self.test_user,
            title=self.test_title,
            description=self.test_description
        )

        self.client.force_login(self.test_user)
        delete_url = reverse('delete', args=[test_task.pk])
        response = self.client.delete(delete_url)

        self.assertEqual(
            response.status_code,
            HTTPStatus.FOUND,
            'При удалении задачи возвращен код страницы, отличный от 302.'
        )
