import pytest
from django.contrib.auth.models import User
from django.test import TestCase

from tracker.models import Task, Tags, TaskTag


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

        self.test_user = User.objects.create(
            username='test_user',
            password='test_password'
        )
        self.test_task = Task.objects.create(author=self.test_user)
        self.test_tag = Tags.objects.create(name='test_tag', slug='test_slug')
        self.test_tasktag = TaskTag.objects.create(
            task=self.test_task,
            tag=self.test_tag
        )

    def tearDown(self):
        """Удаляем тестовые данные после прохождения тестов."""

        models_to_delete = [self.test_user, self.test_task,
                            self.test_tag, self.test_tasktag]

        for model in models_to_delete:
            model.delete()

    def test_task_model_has_required_fields(self):
        """Проверяем, что модель Task имеет все необходимые поля."""

        required_fields = ['author', 'title', 'description', 'priority',
                           'status', 'deadline', 'tags']

        for field_name in required_fields:
            self.assertTrue(
                hasattr(self.test_task, field_name),
                f'Поле {field_name} отсутствует в модели Task'
            )

    def test_tags_model_has_required_fields(self):
        """Проверяем, что модель Tags имеет все необходимые поля."""

        required_fields = ['name', 'slug']

        for field_name in required_fields:
            self.assertTrue(
                hasattr(self.test_tag, field_name),
                f'Поле {field_name} отсутствует в модели Tag'
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

        required_fields = ['task', 'tag']

        for field_name in required_fields:
            self.assertTrue(
                hasattr(self.test_tasktag, field_name),
                f'Поле {field_name} отсутствует в модели TaskTag'
            )
