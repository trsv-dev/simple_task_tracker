from django import forms

from tags.models import Tags
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

    tags = forms.ModelMultipleChoiceField(
        queryset=Tags.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'wide-select'}),
        label='Теги',
        required=False,
    )

    class Meta:
        model = Task
        fields = ('title', 'description', 'priority',
                  'status', 'deadline', 'deadline_reminder', 'assigned_to',
                  'tags', 'is_draft')

        labels = {
            'title': 'Название',
            'description': 'Описание',
            'priority': 'Приоритет',
            'status': 'Статус',
            'deadline': 'Дедлайн',
            'deadline_reminder': 'Когда напомнить о дедлайне',
            'assigned_to': 'Ответственный',
            'tags': 'Теги',
            'is_draft': 'Опубликовано?'
        }

        widgets = {
            'is_draft': forms.CheckboxInput(
                attrs={'class': 'checkbox'}
            )
        }
