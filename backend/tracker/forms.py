from django import forms

from tracker.models import Task, Comment, TaskImage, CommentImage


class TaskImageForm(forms.ModelForm):
    """Форма прикрепления изображения к задаче."""

    class Meta:
        model = TaskImage
        fields = ('image',)

        labels = {
            'image': 'Изображение'
        }


class TaskCreateForm(forms.ModelForm):
    """Форма создания задачи."""

    class Meta:
        model = Task
        fields = ('title', 'description', 'priority',
                  'status', 'deadline', 'deadline_reminder', 'assigned_to',
                  )

        labels = {
            'title': 'Название',
            'description': 'Описание',
            'priority': 'Приоритет',
            'status': 'Статус',
            'deadline': 'Дедлайн',
            'deadline_reminder': 'Когда напомнить о дедлайне',
            'assigned_to': 'Ответственный',
        }


class CommentForm(forms.ModelForm):
    """Форма создания комментария."""

    class Meta:
        model = Comment
        fields = ('text',)

    labels = {
        'text': 'Текст'
    }


class CommentImageForm(forms.ModelForm):
    """Форма прикрепления изображения к комментарию."""

    class Meta:
        model = CommentImage
        fields = ('image',)

        labels = {
            'image': 'Изображение'
        }
