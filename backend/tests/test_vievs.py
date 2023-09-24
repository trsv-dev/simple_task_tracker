from django.test import TestCase, Client
from http import HTTPStatus

from django.urls import reverse

from tracker.models import Task
from django.contrib.auth.models import User


class ViewsTestCase(TestCase):
    """Тестируем вьюхи."""

    def setUp(self):
        """Тестовые данные."""

        self.test_user = User.objects.create(
            username='test_user',
            password='test_password'
        )
        self.test_title = 'test_title'
        self.test_description = 'test_description'
        self.test_data = {
            'title': self.test_title,
            'description': self.test_description
        }

    def tearDown(self):
        """Удаляем тестовые данные после прохождения тестов."""

        self.test_user.delete()

    def test_create_task(self):
        """
        Тестируем простое создание задачи от заданного
        существующего пользователя.
        """

        test_task = Task.objects.create(
            author=self.test_user,
            title=self.test_title,
            description=self.test_description
        )
        response = self.client.post(reverse('create'), data=self.test_data)

        created_test_task = Task.objects.get(
            author=self.test_user,
            title=self.test_title,
            description=self.test_description
        )
        self.assertEqual(
            test_task, created_test_task, 'Объект Task не создан!'
        )

    def test_create_task_from_unauthorized_user(self):
        """
        Тестируем создание задачи от имени
        неавторизованного пользователя.
        """

        unauthorized_user = Client()
        response = unauthorized_user.post(
            reverse('create'),
            data=self.test_data,
        )

        self.assertIn(
            response.status_code,
            [HTTPStatus.FOUND, HTTPStatus.FORBIDDEN],
            'Неавторизованный пользователь должен быть переадресован!'
        )

