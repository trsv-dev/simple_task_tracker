from django import forms

from tracker.models import Task, Comment


class TaskCreateForm(forms.ModelForm):
    """Форма создания задачи."""

    class Meta:
        model = Task
        fields = ('title', 'description', 'priority',
                  'status', 'deadline', 'deadline_reminder', 'assigned_to',
                  'image')

        labels = {
            'title': 'Название',
            'description': 'Описание',
            'priority': 'Приоритет',
            'status': 'Статус',
            'deadline': 'Дедлайн',
            'deadline_reminder': 'Когда напомнить о дедлайне',
            'assigned_to': 'Ответственный',
            'image': 'Изображение',
        }


class CommentForm(forms.ModelForm):
    """Форма создания комментария."""

    class Meta:
        model = Comment
        fields = ('text',)

    labels = {
        'text': 'Текст'
    }
