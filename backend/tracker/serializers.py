import json

import locale

from django.core.serializers import serialize
from django.urls import reverse
from django.utils import timezone

from task_tracker.settings import BASE_URL

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')


class TaskSerializer:
    """Кастомный класс для сериализации экземпляра модели Task"""

    def __init__(self, instance):
        """Конструктор класса."""

        self.instance = instance

    # Для того чтобы можно было обращаться к методу 'data' сериализатора через
    # точечную нотацию без скобок - навешиваем декоратор @property.
    @property
    def data(self):
        """Собираем данные воедино."""

        # Вместо возврата строки JSON, возвращаем словарь данных.
        serialized_dict = json.loads(serialize('json', [self.instance]))
        data = serialized_dict[0]['fields']

        data['link'] = self.get_link(self.instance)
        data['author'] = self.get_author()
        data['assigned_to'] = self.get_assigned_to()
        data['deadline'] = self.get_deadline(self.instance)
        if data['done_by_time']:
            data['done_by_time'] = self.get_done_by_time(self.instance)

        return data

    def get_author(self):
        """Получаем юзернейм автора."""

        return self.serialize_user(self.instance.author).get('username')

    def get_assigned_to(self):
        """Получаем юзернейм назначенного на выполнение задачи пользователя."""

        return self.serialize_user(self.instance.assigned_to).get('username')

    def serialize_user(self, user):
        """Сериализация данных о пользователе."""
        return {'id': user.id, 'username': user.username, 'email': user.email}

    def get_link(self, instance):
        """Получение прямой ссылки на задачу."""

        task_pk = instance.id
        task_url = reverse('tracker:detail', args=[task_pk])

        return BASE_URL + task_url

    def get_deadline(self, instance):
        """Получение дедлайна в привычном формате."""

        deadline = instance.deadline

        local_deadline = deadline.astimezone(
            timezone.get_current_timezone())

        return local_deadline.strftime('%d %B %Y г. %H:%M')

    def get_done_by_time(self, instance):
        """Получение времени выполнения задачи в привычном формате."""

        done_by_time = instance.done_by_time

        local_done_by_time = done_by_time.astimezone(
            timezone.get_current_timezone())

        return local_done_by_time.strftime('%d %B %Y г. %H:%M')


class UserSerializer:
    """
    Кастомный класс для сериализации экземпляра модели User - пользователя,
    которому отправляется письмо об упоминании.
    """

    def __init__(self, instance):
        """Конструктор класса."""

        self.instance = instance

    # Для того чтобы можно было обращаться к методу 'data' сериализатора через
    # точечную нотацию без скобок - навешиваем декоратор @property.
    @property
    def data(self):
        """Собираем данные воедино."""

        # Вместо возврата строки JSON, возвращаем словарь данных.
        serialized_dict = json.loads(serialize('json', [self.instance]))
        data = serialized_dict[0]['fields']

        return data


# import locale
#
# from django.urls import reverse
# from django.utils import timezone
# from rest_framework import serializers
#
# from task_tracker.settings import BASE_URL
# from tracker.models import Task, User
#
# locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
#
#
# class TaskSerializer(serializers.ModelSerializer):
#     """
#     Сериализатор для задачи (task), письмо о дедлайне
#     которой отправляется в Celery.
#     """
#
    # author = serializers.StringRelatedField(read_only=True)
#     assigned_to = serializers.StringRelatedField(read_only=True)
#     link = serializers.SerializerMethodField()
#
#     class Meta:
#         model = Task
#         fields = '__all__'
#
#     def get_link(self, instance):
#         """Получение прямой ссылки на задачу."""
#
#         # Передаем словарь только в случае удаления задачи для сохранения
#         # данных из экземпляра перед удалением.
#
#         if isinstance(instance, dict):
#             task_pk = instance.get('id')
#         else:
#             task_pk = instance.id
#         task_url = reverse('tracker:detail', args=[task_pk])
#
#         return BASE_URL + task_url
#
#     def to_representation(self, instance):
#         """Показываем дедлайн в привычном формате."""
#
#         representation = super().to_representation(instance)
#
#         # Передаем словарь только в случае удаления задачи для сохранения
#         # данных из экземпляра перед удалением.
#
#         if isinstance(instance, dict):
#             deadline = instance.get('deadline')
#         else:
#             deadline = instance.deadline
#
#         local_deadline = deadline.astimezone(
#             timezone.get_current_timezone())
#
#         representation['deadline'] = local_deadline.strftime(
#             '%d %B %Y г. %H:%M'
#         )
#         return representation
#
#
# class UserSerializer(serializers.ModelSerializer):
#     """
#     Сериализатор для пользователя, которому
#     отправляется письмо об упоминании.
#     """
#
#     username = serializers.StringRelatedField(read_only=True)
#
#     class Meta:
#         model = User
#         fields = '__all__'
