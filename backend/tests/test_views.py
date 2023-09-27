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
        self.test_not_author = User.objects.create_user(
            username='test_not_author'
        )
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_not_author = Client()
        self.authorized_client.force_login(self.test_user)
        self.authorized_client_not_author.force_login(self.test_not_author)

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
        self.edited_data = {
            'title': 'Измененное название тестовой задачи',
            'description': 'Измененное описание тестовой задачи',
            'priority': 'Высокий',
            'status': 'В процессе выполнения',
            'deadline': '2100-01-01 00:00:00',
        }

    def tearDown(self):
        """Удаляем тестовые данные после прохождения тестов."""

        self.authorized_client.logout()
        self.authorized_client_not_author.logout()
        self.test_user.delete()
        self.test_not_author.delete()

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

    def test_create_task_by_authorized_user(self):
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

    def test_edit_task_by_author(self):
        """Тестируем редактирование задачи автором."""

        test_task = Task.objects.create(
            author=self.test_user,
            title=self.test_title,
            description=self.test_description
        )

        edit_url = reverse('edit', args=[test_task.id])
        response_with_context = self.authorized_client.get(edit_url)

        edit_response = self.authorized_client.post(edit_url, self.edited_data)
        edited_task = Task.objects.get(pk=test_task.pk)

        self.assertNotEqual(
            test_task.title,
            edited_task.title,
            'Задача до и после редактирования должны различаться!'
        )

        self.assertEqual(
            edit_response.status_code,
            HTTPStatus.FOUND,
            'После редактирования задачи должен '
            'происходить редирект на главную страницу! (временно)'
        )
        print(response_with_context.context)
        self.assertEqual(
            response_with_context.context['task'],
            test_task,
            'Контекст должен содержать задачу, которую мы редактировали.'
        )

    def test_edit_task_by_other_user(self):
        """Тестируем редактирование задачи не автором."""

        test_task = Task.objects.create(
            author=self.test_user,
            title=self.test_title,
            description=self.test_description
        )

        url = reverse('edit', args=[test_task.pk])
        response = self.authorized_client_not_author.post(
            url, self.edited_data
        )

        edited_task = Task.objects.get(pk=test_task.pk)

        self.assertEqual(
            edited_task,
            test_task,
            'Не автор не может изменить задачу!'
        )

        self.assertEqual(
            response.status_code,
            HTTPStatus.FOUND,
            'Не автор при попытке изменения задачи '
            'должен быть переадресован на главную страницу!'
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
            'происходить редирект на главную страницу! (временно)'
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
            'происходить редирект на главную страницу! (временно)'
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
