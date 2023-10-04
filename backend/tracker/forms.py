from django import forms

from tracker.models import Task


class TaskCreateForm(forms.ModelForm):
    """Форма создания задачи."""

    class Meta:
        model = Task
        fields = ('title', 'description', 'priority',
                  'status', 'deadline', 'assigned_to')

        labels = {
            'title': 'Название',
            'description': 'Описание',
            'priority': 'Приоритет',
            'status': 'Статус',
            'deadline': 'Дедлайн',
            'assigned_to': 'Ответственный',
        }
