from django.http import HttpResponseRedirect
from django.utils import timezone

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django_celery_beat.models import (IntervalSchedule, CrontabSchedule,
                                       SolarSchedule, ClockedSchedule,
                                       PeriodicTask)

from tracker.models import Task, Tags, TaskTag, Comment

admin.site.site_header = "Трекер задач"
admin.site.site_title = "Панель администрирования"
admin.site.index_title = "Добро пожаловать в трекер задач"

# Убираем ненужные модули Celery Beat из админки
admin.site.unregister(SolarSchedule)
admin.site.unregister(ClockedSchedule)
admin.site.unregister(PeriodicTask)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(CrontabSchedule)


class TagsInLine(admin.TabularInline):
    model = Task.tags.through


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Класс администрирования задач."""

    def show_tags(self, object):
        """Показывать тэги."""

        return '\n'.join(tag.name for tag in object.tags.all())

    show_tags.short_description = 'Теги'

    list_display = (
        'id', 'author', 'get_title', 'get_description', 'show_tags',
        'priority', 'status', 'previous_status', 'assigned_to',
        'created', 'deadline', 'deadline_reminder', 'is_notified',
        'is_done', 'done_by', 'done_by_time')

    fieldsets = (
        ('Информация о задаче', {
            'fields': (
                'author', 'title', 'description',
                'priority', 'status', 'previous_status', 'assigned_to',
                'deadline', 'deadline_reminder', 'is_notified',
            ),
        }),
        ('Детали выполнения задачи', {
            'description': 'Как правило, здесь вмешательство не требуется. '
                           'Но если помечаете задачу выполненной - '
                           'ОБЯЗАТЕЛЬНО указывайте выполнившего пользователя '
                           'и дату выполнения не ранее даты создания задачи!',
            'fields': ('is_done', 'done_by', 'done_by_time'),
            'classes': ('collapse', 'errornote'),
        }),
    )

    # readonly_fields = ('is_done', 'done_by', 'done_by_time')

    search_fields = ('author__username', 'author__email',
                     'description', 'title')
    ordering = ('-created',)
    inlines = (TagsInLine,)

    def get_title(self, obj):
        """Обрезаем длинные заголовки."""

        return obj.title[:30] + ('...' if len(obj.title) > 30 else '')

    get_title.short_description = 'название'

    def get_description(self, obj):
        """Обрезаем длинные описания."""

        return (obj.description[:40] +
                ('...' if len(obj.description) > 40 else ''))

    get_description.short_description = 'описание'

    def validate_done_fields(self, obj):
        """
        Проверяем, что при ручной отметке задачи как выполненной будет
        соблюден ряд условий - будет выбран пользователь,
        выполнивший задачу и адекватное время выполнения.
        """

        if obj.is_done and (not obj.done_by or not obj.done_by_time):
            raise ValidationError('При отметке задания выполненным из '
                                  'админки необходимо указать выполнившего '
                                  'задачу пользователя и время выполнения!')
        elif obj.done_by_time > timezone.now():
            raise ValidationError('Время выполнения задачи не может '
                                  'быть в будущем!')
        elif obj.created > obj.done_by_time:
            raise ValidationError('Время выполнения задачи не может быть '
                                  'раньше времени создания задачи!')
        else:
            return obj

    def response_change(self, request, obj):
        """
        Переопределяем порядок действий при редактировании задачи,
        а конкретнее - при нажатии кнопки 'Сохранить' в режиме
        редактирования задачи.
        """

        # Если была нажата кнопка "Сохранить"
        if "_save" in request.POST:
            try:
                # Если задача была отмечена как выполненная,
                # то проверяем указан ли выполнивший ее пользователь
                # и время выполнения.
                self.validate_done_fields(obj)
                obj.save()
            except ValidationError as e:
                self.message_user(request, e.message, messages.ERROR)
                return HttpResponseRedirect(request.path_info)
        return super().response_change(request, obj)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_task', 'author', 'get_text', 'created')
    ordering = ('created',)
    search_fields = ('task__author__username', 'task__author__email', 'text')

    def get_text(self, obj):
        """Обрезаем длинные комментарии."""

        return obj.text[:50] + ('...' if len(obj.text) > 50 else '')

    def get_task(self, obj):
        """Обрезаем длинные заголовки задачи."""

        return (obj.task.title[:50] +
                ('...' if len(obj.task.title) > 50 else ''))

    get_text.short_description = 'текст'
    get_task.short_description = 'задача'


@admin.register(TaskTag)
class TaskTagsAdmin(admin.ModelAdmin):
    list_display = ('task', 'tag')


@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
