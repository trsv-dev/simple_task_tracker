import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.test import Client
from django.utils import timezone

from tracker.models import (Task, Tags, TaskTag, PRIORITY,
                            HIGH, MEDIUM, LOW, PENDING)

User = get_user_model()


def test_tasktag_model_exists():
    """Проверяем наличие модели TaskTag."""

    try:
        from tracker.models import TaskTag
        assert TaskTag is not None
    except ImportError:
        pytest.fail('Модель TaskTag не найдена в tracker.models')


def test_tags_model_exists():
    """Проверяем наличие модели Tags."""

    try:
        from tracker.models import Tags
        assert Tags is not None
    except ImportError:
        pytest.fail('Модель Tags не найдена в tracker.models')


def test_task_model_exists():
    """Проверяем наличие модели Task."""

    try:
        from tracker.models import Task
        assert Task is not None
    except ImportError:
        pytest.fail('Модель Task не найдена в tracker.models')


class ModelsTestCase(TestCase):
    """Тестируем модели."""

    def setUp(self):
        """Тестовые данные."""

        self.test_user = User.objects.create_user(
            username='test_user'
        )
        self.authorized_client = Client()
        self.authorized_client.force_login(self.test_user)

        self.test_title = 'Тестовая задача'
        self.test_description = 'Описание тестовой задачи'
        self.test_task = Task.objects.create(
            author=self.test_user,
            title=self.test_title,
            description=self.test_description
        )

        self.edited_data = {
            'title': 'Измененное название тестовой задачи',
            'description': 'Измененное описание тестовой задачи',
            'priority': 'Высокий',
            'status': 'В процессе выполнения',
            'deadline': '2100-01-01 00:00:00',
        }

        self.test_tag = Tags.objects.create(name='test_tag', slug='test_slug')
        self.test_tasktag = TaskTag.objects.create(
            task=self.test_task,
            tag=self.test_tag
        )

    def tearDown(self):
        """Удаляем тестовые данные после прохождения тестов."""

        instances_to_delete = (self.test_user, self.test_task,
                               self.test_tag, self.test_tasktag)

        for instance in instances_to_delete:
            instance.delete()

    def test_task_model_has_required_fields(self):
        """Проверяем, что модель Task имеет все необходимые поля."""

        task = self.test_task
        task_fields = [field.name for field in task._meta.get_fields()]
        required_fields = ['author', 'title', 'description', 'priority',
                           'status', 'deadline', 'tags']

        for field in required_fields:
            with self.subTest(field=field):
                self.assertIn(
                    field,
                    task_fields,
                    msg=f'Поле {field} отсутствует в модели Task!'
                )

    def test_labels_have_correct_names(self):
        """Проверяем, что verbose_names совпадают с ожидаемыми."""

        task = self.test_task
        verbose_names = {
            'author': 'Автор',
            'title': 'Название',
            'description': 'Описание',
            'priority': 'Приоритет',
            'status': 'Статус',
            'created': 'Время создания',
            'deadline': 'Дедлайн',
            'tags': 'Тег'
        }

        for field, expected_value in verbose_names.items():
            with self.subTest(field=field):
                self.assertEqual(
                    task._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_labels_have_correct_help_text(self):
        """Проверяем, что help_text совпадает с ожидаемым."""

        task = self.test_task
        help_text = {
            'author': 'Выберите автора',
            'title': 'Введите название задачи',
            'description': 'Введите описание задачи',
            'priority': 'Установите приоритет',
            'status': 'Выберите статус',
            'tags': 'Выберите подходящий тег'
        }

        for field, expected_value in help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    task._meta.get_field(field).help_text,
                    expected_value
                )

    def test_task_model_return_title(self):
        """
        Проверяем, что метод __str__ класса Task возвращает
        строковый заголовок.
        """

        task = Task.objects.get(pk=self.test_task.pk)
        self.assertEqual(
            task.__str__(),
            'Тестовая задача',
            msg='Должен возвращаться заголовок задачи в виде строки (str)!'
        )

    def test_task_model_return_str_title(self):
        """Проверяем, что модель Task возвращает заголовок."""

        task = Task.objects.get(pk=self.test_task.pk)
        self.assertEqual(
            task.title,
            'Тестовая задача',
            msg='Должен возвращаться заголовок задачи!'
        )

    def test_task_model_return_colors(self):
        """Проверяем, что модель Task возвращает цвета."""

        for priority, expected_color in [(HIGH, 'red'),
                                         (MEDIUM, 'blue'), (LOW, 'green')]:
            task = Task.objects.create(
                author=self.test_user,
                title=self.test_title,
                description=self.test_description,
                priority=priority,
                status=PENDING,
                deadline=timezone.now()
            )

            model_color = task.get_priority_color()

            self.assertEqual(
                model_color,
                expected_color,
                f'Цвет приоритета {model_color} не совпадает с '
                f'ожидаемым {expected_color}!'
            )

    def test_tags_model_has_required_fields(self):
        """Проверяем, что модель Tags имеет все необходимые поля."""

        tag = self.test_tag
        tag_fields = [field.name for field in tag._meta.get_fields()]
        required_fields = ['name', 'slug']

        for field in required_fields:
            with self.subTest(field=field):
                self.assertIn(
                    field,
                    tag_fields,
                    f'Поле {field} отсутствует в модели Tag'
                )

    def test_tags_model_return_str_title(self):
        """Проверяем, что метод __str__ класса Tag возвращает строковое имя."""

        tag = Tags.objects.get(pk=self.test_tag.pk)
        self.assertEqual(
            tag.__str__(),
            'test_tag',
            msg='Должно возвращаться имя тега в виде строки (str)!'
        )

    def test_task_and_tag_is_instances(self):
        """
        Проверяем, являются ли 'task' и 'tag' в tasktag экземплярами
        соответствующих классов.
        """

        task_example = self.test_tasktag.task
        tag_example = self.test_tasktag.tag

        self.assertIsInstance(
            task_example,
            Task,
            'task_example не является экземпляром класса Task'
        )
        self.assertIsInstance(
            tag_example,
            Tags,
            'tag_example не является экземпляром класса Tag'
        )

    def test_tasktag_model_has_required_fields(self):
        """Проверяем, что модель TaskTag имеет все необходимые поля."""

        tasktag = self.test_tasktag
        tasktag_fields = [field.name for field in tasktag._meta.get_fields()]
        required_fields = ['task', 'tag']

        for field in required_fields:
            with self.subTest(field=field):
                self.assertIn(
                    field,
                    tasktag_fields,
                    f'Поле {field} отсутствует в модели TaskTag'
                )
