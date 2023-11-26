import locale

from django.urls import reverse
from django.utils import timezone
from rest_framework import serializers

from task_tracker.settings import BASE_URL
from tracker.models import Task, User

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')


class TaskSerializer(serializers.ModelSerializer):
    """
    Сериализатор для задачи (task), письмо о дедлайне
    которой отправляется в Celery.
    """

    author = serializers.StringRelatedField(read_only=True)
    assigned_to = serializers.StringRelatedField(read_only=True)
    link = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = '__all__'

    def get_link(self, instance):
        """Получение прямой ссылки на задачу."""

        # Передаем словарь только в случае удаления задачи для сохранения
        # данных из экземпляра перед удалением.

        if isinstance(instance, dict):
            task_pk = instance.get('id')
        else:
            task_pk = instance.id
        task_url = reverse('tracker:detail', args=[task_pk])

        return BASE_URL + task_url

    def to_representation(self, instance):
        """Показываем дедлайн в привычном формате."""

        representation = super().to_representation(instance)

        # Передаем словарь только в случае удаления задачи для сохранения
        # данных из экземпляра перед удалением.

        if isinstance(instance, dict):
            deadline = instance.get('deadline')
        else:
            deadline = instance.deadline

        local_deadline = deadline.astimezone(
            timezone.get_current_timezone())

        representation['deadline'] = local_deadline.strftime(
            '%d %B %Y г. %H:%M'
        )
        return representation


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для пользователя, которому
    отправляется письмо об упоминании.
    """

    username = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = User
        fields = '__all__'
