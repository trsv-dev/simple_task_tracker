from django import forms
from django.forms import RadioSelect

from tracker.models import Task, Tags


class TaskCreateForm(forms.ModelForm):
    """Форма создания задачи."""

    class Meta:
        model = Task
        fields = ('title', 'description', 'priority',
                  'status', 'deadline')
