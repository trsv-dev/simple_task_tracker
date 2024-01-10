from django.contrib import admin
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
    def show_tags(self, object):
        return '\n'.join(tag.name for tag in object.tags.all())

    show_tags.short_description = 'Теги'

    list_display = (
        'id', 'author', 'get_title', 'get_description', 'show_tags',
        'priority', 'status', 'previous_status', 'assigned_to',
        'created', 'deadline', 'deadline_reminder', 'is_notified',
        'is_done', 'done_by', 'done_by_time')

    readonly_fields = ('is_done', 'done_by', 'done_by_time')

    search_fields = ('author__username', 'author__email',
                     'description', 'title')
    ordering = ('-created',)
    inlines = (TagsInLine,)

    def get_title(self, obj):
        return obj.title[:30]

    get_title.short_description = 'название'

    def get_description(self, obj):
        return obj.description[:40]

    get_description.short_description = 'описание'

    # def validate_done_fields(self, obj):
    #     if obj.is_done and (not obj.done_by or not obj.done_by_time):
    #         raise ValidationError('При отметке задания выполненным из '
    #                               'админки необходимо указать выполнившего '
    #                               'задачу пользователя и время выполнения')
    #
    # def save_model(self, request, obj, form, change):
    #     try:
    #         self.validate_done_fields(obj)
    #     except ValidationError as e:
    #         self.message_user(request, message=e.message, level='ERROR')
    #         return
    #     super().save_model(request, obj, form, change)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_task', 'author', 'get_text', 'created')
    ordering = ('created',)
    search_fields = ('task__author__username', 'task__author__email', 'text')

    def get_text(self, obj):
        return obj.text[:50]

    def get_task(self, obj):
        return obj.task.title[:50]

    get_text.short_description = 'текст'
    get_task.short_description = 'задача'


@admin.register(TaskTag)
class TaskTagsAdmin(admin.ModelAdmin):
    list_display = ('task', 'tag')


@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
