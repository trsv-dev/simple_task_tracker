from django import forms
from django.contrib.auth.models import User
from django.forms import RadioSelect

from tracker.models import Task, Tags


class TaskCreateForm(forms.ModelForm):
    """Форма создания задачи."""

    class Meta:
        model = Task
        fields = ('title', 'description', 'priority',
                  'status', 'deadline', 'assigned_to')

    def __init__(self, *args, **kwargs):
        super(TaskCreateForm, self).__init__(*args, **kwargs)

        self.fields['assigned_to'] = forms.ModelChoiceField(
            queryset=User.objects.all(),
            widget=forms.Select,
        )
