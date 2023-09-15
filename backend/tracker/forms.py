from django import forms

from tracker.models import Task


class TaskCreateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ('title', 'description', 'priority', 'status', 'deadline')
