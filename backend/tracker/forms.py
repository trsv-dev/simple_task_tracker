from django import forms

from tracker.models import Task


# class TaskImageForm(forms.ModelForm):
#     """Форма прикрепления изображения к задаче."""
#
#     class Meta:
#         model = TaskImage
#         fields = ('image',)
#
#         labels = {
#             'image': 'Изображение'
#         }


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
