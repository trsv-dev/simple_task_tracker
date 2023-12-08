from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from tracker.models import Task

User = get_user_model()


class ViewsTestCase(TestCase):
    """Тестируем вьюхи."""

    def setUp(self):
        """Тестовые данные."""

        self.test_user = User.objects.create_user(
            username='test_user',
            email='test_user@test.test'
        )
        self.test_not_author = User.objects.create_user(
            username='test_not_author',
            email='test_not_author@test.test'
        )
        self.test_admin_user = User.objects.create_user(
            username='test_admin_user',
            email='test_admin_user@test.test',
            is_staff=True
        )
        self.test_assigned_to_user = User.objects.create_user(
            username='assigned_to_user',
            email='assigned_to_user@test.test'
        )
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_not_author = Client()
        self.authorized_client_admin = Client()
        self.authorized_client_assigned_to_user = Client()
        self.authorized_client.force_login(self.test_user)
        self.authorized_client_not_author.force_login(self.test_not_author)
        self.authorized_client_admin.force_login(self.test_admin_user)
        self.authorized_client_assigned_to_user.force_login(
            self.test_assigned_to_user
        )

        self.test_title = 'Тестовая задача'
        self.test_description = 'Описание тестовой задачи'

        self.test_task = Task.objects.create(
            author=self.test_user,
            title=self.test_title,
            description=self.test_description,
            assigned_to=self.test_assigned_to_user,
        )

        self.test_data = {
            'title': 'Тестовая задача 2',
            'description': 'Описание тестовой задачи 2',
            'priority': 'Высокий',
            'status': 'Ожидает выполнения',
            'previous_status': '',
            'assigned_to': self.test_user.id,
            'deadline': '2100-01-01 00:00:00',
            'deadline_reminder': '2099-12-31T00:00',
            'is_done': 'False',
            'done_by': '',
            'done_by_time': ''
        }
        self.edited_data = {
            'title': 'Измененное название тестовой задачи',
            'description': 'Измененное описание тестовой задачи',
            'priority': 'Высокий',
            'status': 'В процессе выполнения',
            'previous_status': 'Ожидает выполнения',
            # Для 'assigned_to' используем self.test_user.id или '1',
            # т.к. в модели ForeignKey, а это значит что значение поля
            # будет равняться id пользователя по умолчанию.
            'assigned_to': self.test_not_author.id,
            'deadline': '2100-01-01 00:00:00',
            'deadline_reminder': '2099-12-31T00:00',
            'is_done': 'False',
            'done_by': '',
            'done_by_time': ''
        }
        self.invalid_data = {
            'title': '',
            'description': 'Описание тестовой задачи',
            'priority': 'Высокий',
            'status': 'В процессе выполнения',
            'previous_status': 'Ожидает выполнения',
            'assigned_to': self.test_assigned_to_user.id,
            'deadline': '2100-01-01 00:00:00',
            'deadline_reminder': '2099-01-01T01:00',
            'is_done': 'False',
            'done_by': '',
            'done_by_time': ''
        }

    def tearDown(self):
        """Удаляем тестовые данные после прохождения тестов."""

        self.test_task.delete()
        self.authorized_client.logout()
        self.authorized_client_not_author.logout()
        self.authorized_client_admin.logout()
        self.test_user.delete()
        self.test_not_author.delete()
        self.test_admin_user.delete()
        self.authorized_client_assigned_to_user.logout()
        self.test_assigned_to_user.delete()

    def test_homepage_by_guest_client(self):
        """Тестируем доступность главной страницы."""

        response = self.guest_client.get(reverse('tracker:index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_page_by_authorized_client(self):
        """
        Тестируем доступность страницы создания задачи
        для авторизованного пользователя.
        """

        response = self.authorized_client.get(reverse('tracker:create'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_task_by_authorized_user(self):
        """
        Тестируем простое создание задачи от заданного
        существующего пользователя.
        """

        response = self.authorized_client.post(
            reverse('tracker:create'),
            data=self.test_data
        )

        # Значение будет равно 1, т.к. в тестовых данных создается задача,
        # т.е. нужно вычесть 1 из общего кол-ва.
        tasks_count = Task.objects.count() - 1
        created_test_task = Task.objects.last()
        assigned_to_id = created_test_task.assigned_to.id

        self.assertEqual(
            tasks_count,
            1,
            msg='Задача должна создаваться!'
        )

        self.assertTrue(
            Task.objects.filter(
                title='Тестовая задача 2',
                author=self.test_user
            ).exists()
        )

        self.assertEqual(
            created_test_task.author,
            self.test_user,
            msg='Автор задачи должен быть установлен корректно!'
        )

        self.assertEqual(
            assigned_to_id,
            self.test_user.id,
            msg='Исполнитель по умолчанию должен быть равен текущему юзеру!'
        )

        self.assertRedirects(response, reverse('tracker:index'))

    def test_create_task_with_invalid_form(self):
        """Тестируем создание задачи с невалидной формой."""

        # Значение будет равно 1, т.к. в тестовых данных создается задача,
        # т.е. нужно вычесть 1 из общего кол-ва.
        tasks_count = Task.objects.count() - 1

        response = self.authorized_client.post(
            reverse('tracker:create'),
            data=self.invalid_data
        )

        form = response.context['form']

        self.assertFormError(
            form,
            'title',
            'Обязательное поле.'
        )

        self.assertNotEqual(
            tasks_count,
            1,
            msg='Невалидная форма не должна приводить к созданию задачи!')

        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            msg='Должна возвращаться страница создания задачи!'
        )

    def test_create_task_by_unauthorized_user(self):
        """
        Тестируем создание задачи от имени
        неавторизованного пользователя.
        """

        unauthorized_user = Client()
        response = unauthorized_user.post(
            reverse('tracker:create'),
            data=self.test_data,
        )

        # Значение будет равно 1, т.к. в тестовых данных создается задача,
        # т.е. нужно вычесть 1 из общего кол-ва.
        tasks_count = Task.objects.count() - 1

        self.assertTrue(
            tasks_count == 0,
            msg='Задача не должна создаваться неавторизованным пользователем!'
        )

        self.assertEqual(
            response.status_code,
            HTTPStatus.FOUND,
            msg='Неавторизованный пользователь должен быть переадресован!'
        )

    def test_edit_task_by_author(self):
        """Тестируем редактирование задачи автором."""

        edit_url = reverse('tracker:edit', args=[self.test_task.id])
        response_with_context = self.authorized_client.get(edit_url)

        edit_response = self.authorized_client.post(edit_url, self.edited_data)
        edited_task = Task.objects.get(pk=self.test_task.pk)

        self.assertNotEqual(
            self.test_task.title,
            edited_task.title,
            'Задача до и после редактирования должны различаться!'
        )

        self.assertRedirects(edit_response, reverse('tracker:detail',
                                                    args=[self.test_task.id]))

        self.assertEqual(
            response_with_context.context['task'],
            self.test_task,
            'Контекст должен содержать задачу, которую мы редактировали!'
        )

    def test_edit_task_by_other_user(self):
        """Тестируем редактирование задачи не автором."""

        edit_url = reverse('tracker:edit', args=[self.test_task.pk])
        response = self.authorized_client_not_author.post(
            edit_url, self.edited_data
        )

        edited_task = Task.objects.get(pk=self.test_task.pk)

        self.assertEqual(
            edited_task,
            self.test_task,
            'Не автор не может изменить задачу!'
        )

        self.assertRedirects(response, reverse('tracker:index'))

    def test_edit_task_by_admin(self):
        """Тестируем редактирование задачи админом."""

        edit_url = reverse('tracker:edit', args=[self.test_task.id])
        response_with_context = self.authorized_client_admin.get(edit_url)

        edit_response = self.authorized_client_admin.post(
            edit_url, self.edited_data
        )
        edited_task = Task.objects.get(pk=self.test_task.pk)

        self.assertNotEqual(
            edited_task.title,
            self.test_task.title,
            msg='Задача до и после редактирования должны различаться!'
        )

        self.assertRedirects(edit_response, reverse('tracker:detail',
                                                    args=[self.test_task.id]))

        self.assertEqual(
            response_with_context.context['task'],
            self.test_task,
            'Контекст должен содержать задачу, которую мы редактировали!'
        )

    def test_edit_task_by_assigned_to_user(self):
        """Тестируем редактирование задачи ответственным пользователем."""

        edit_url = reverse('tracker:edit', args=[self.test_task.id])
        response_with_context = self.authorized_client_assigned_to_user.get(
            edit_url
        )

        edit_response = self.authorized_client_assigned_to_user.post(
            edit_url,
            self.edited_data
        )
        edited_task = Task.objects.get(pk=self.test_task.pk)

        self.assertNotEqual(
            edited_task.title,
            self.test_task.title,
            msg='Задача до и после редактирования должны различаться!'
        )

        self.assertRedirects(edit_response, reverse('tracker:detail',
                                                    args=[self.test_task.id]))

        self.assertEqual(
            response_with_context.context['task'],
            self.test_task,
            'Контекст должен содержать задачу, которую мы редактировали!'
        )

    def test_delete_task_by_author(self):
        """Тестируем удаление задачи от существующего пользователя."""

        delete_url = reverse(
            'tracker:delete',
            args=[self.test_task.pk]
        )
        # Из-за того, что @require_POST исмользуем .post, а не .delete
        response = self.authorized_client.post(delete_url)

        task_count = Task.objects.count()

        self.assertTrue(
            task_count == 0,
            'Задача должна удаляться автором'
        )

        self.assertRedirects(response, reverse('tracker:index'))

    def test_delete_task_by_other_user(self):
        """
        Проверка удаления задачи от имени пользователя,
        отличного от автора задачи.
        """

        delete_url = reverse(
            'tracker:delete',
            args=[self.test_task.pk]
        )

        # response = self.authorized_client_not_author.delete(delete_url)
        # Из-за того, что @require_POST исмользуем .post, а не .delete
        response = self.authorized_client_not_author.post(delete_url)

        self.assertRedirects(response, reverse('tracker:index'))

    def test_delete_task_by_admin(self):
        """Тестируем удаление задачи админом."""

        # Счетчик будет равен 1, т.к. в тестовых данных мы создаем задачу.
        task_count_before = Task.objects.count()

        delete_url = reverse(
            'tracker:delete',
            args=[self.test_task.pk]
        )

        response = self.authorized_client_admin.post(delete_url)

        task_count_after = Task.objects.count()

        self.assertNotEqual(
            task_count_after,
            task_count_before,
            msg='Задача должна удаляться админом!')

        self.assertRedirects(response, reverse('tracker:index'))

    def test_delete_task_by_assigned_to_user(self):
        """Тестируем удаление задачи ответственным пользователем."""

        task_count_before = Task.objects.count()

        delete_url = reverse(
            'tracker:delete',
            args=[self.test_task.pk]
        )

        response = self.authorized_client_assigned_to_user.post(delete_url)

        task_count_after = Task.objects.count()

        self.assertNotEqual(
            task_count_after,
            task_count_before,
            msg='Задача должна удаляться ответственным пользователем!'
        )

        self.assertRedirects(response, reverse('tracker:index'))

    def test_task_delete_response_status(self):
        """Тестируем статус ответа при удалении задачи."""

        delete_url = reverse(
            'tracker:delete',
            args=[self.test_task.pk]
        )
        response = self.client.delete(delete_url)

        self.assertEqual(
            response.status_code,
            HTTPStatus.FOUND,
            'При удалении задачи возвращен код страницы, отличный от 302.'
        )

    def test_change_task_assigned_to_by_author(self):
        """
        Тестируем смену пользователя, ответственного за
        выполнение задачи.
        """

        old_assigned_to = self.test_task.assigned_to

        edit_url = reverse('tracker:edit', args=[self.test_task.pk])
        edit_response = self.authorized_client.post(edit_url, self.edited_data)

        edited_task = Task.objects.get(pk=self.test_task.pk)
        new_assigned_to = edited_task.assigned_to

        self.assertNotEqual(
            new_assigned_to,
            old_assigned_to,
            msg='Ответственный за задачу пользователь должен '
                'смениться при его изменении.'
        )

    def test_task_mark_as_done_by_author(self):
        """Тестируем отметку задачи как выполненной автором."""

        is_done_before = self.test_task.is_done

        done_url = reverse(
            'tracker:mark_as_done',
            args=[self.test_task.pk]
        )
        response = self.authorized_client.post(done_url)

        is_done_after = Task.objects.get(pk=self.test_task.pk).is_done

        self.assertNotEqual(
            is_done_after,
            is_done_before,
            msg='Задача должна быть помечена как выполненная!'
        )

        self.assertRedirects(response, reverse('tracker:index'))

    def test_task_mark_as_done_by_admin(self):
        """Тестируем отметку задачи как выполненной автором."""

        is_done_before = self.test_task.is_done

        done_url = reverse(
            'tracker:mark_as_done',
            args=[self.test_task.pk]
        )
        response = self.authorized_client_admin.post(done_url)

        is_done_after = Task.objects.get(pk=self.test_task.pk).is_done

        self.assertNotEqual(
            is_done_after,
            is_done_before,
            msg='Задача должна быть помечена как выполненная!'
        )

        self.assertRedirects(response, reverse('tracker:index'))

    def test_task_mark_as_undone_by_author(self):
        """Тестируем снятие отметки 'выполнено' с задачи автором."""

        done_url = reverse(
            'tracker:mark_as_done',
            args=[self.test_task.pk]
        )
        response = self.authorized_client.post(done_url)
        done_task = Task.objects.get(pk=self.test_task.pk)

        undone_url = reverse(
            'tracker:mark_as_undone',
            args=[self.test_task.pk]
        )
        response = self.authorized_client.post(undone_url)
        undone_task = Task.objects.get(pk=self.test_task.pk)

        self.assertNotEqual(
            done_task.is_done,
            undone_task.is_done,
            msg='Задача должна быть помечена как невыполненная!'
        )

        self.assertRedirects(response, reverse('tracker:index'))

    def test_task_mark_as_undone_by_admin(self):
        """Тестируем снятие отметки 'выполнено' с задачи автором."""

        done_url = reverse(
            'tracker:mark_as_done',
            args=[self.test_task.pk]
        )
        response = self.authorized_client_admin.post(done_url)
        done_task = Task.objects.get(pk=self.test_task.pk)

        undone_url = reverse(
            'tracker:mark_as_undone',
            args=[self.test_task.pk]
        )
        response = self.authorized_client_admin.post(undone_url)
        undone_task = Task.objects.get(pk=self.test_task.pk)

        self.assertNotEqual(
            done_task.is_done,
            undone_task.is_done,
            msg='Задача должна быть помечена как невыполненная!'
        )

        self.assertRedirects(response, reverse('tracker:index'))
