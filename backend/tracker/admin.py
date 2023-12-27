from django.contrib import admin

from tracker.models import Task, Tags, TaskTag, Comment

admin.site.site_header = "Трекер задач"
admin.site.site_title = "Панель администрирования"
admin.site.index_title = "Добро пожаловать в трекер задач"


class TagsInLine(admin.TabularInline):
    model = Task.tags.through


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    def show_tags(self, object):
        return '\n'.join(tag.name for tag in object.tags.all())

    show_tags.short_description = 'Теги'

    list_display = ('id', 'author', 'title', 'description', 'show_tags',
                    'priority', 'status', 'previous_status', 'assigned_to',
                    'created', 'deadline', 'deadline_reminder', 'is_notified',
                    'is_done', 'done_by', 'done_by_time')
    readonly_fields = ('previous_status',)
    search_fields = ('author__username', 'author__email',
                     'description', 'title')
    ordering = ('-created',)
    inlines = (TagsInLine,)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'author', 'id', 'text', 'created')
    ordering = ('created',)
    search_fields = ('task__author__username', 'task__author__email', 'text')


@admin.register(TaskTag)
class TaskTagsAdmin(admin.ModelAdmin):
    list_display = ('task', 'tag')


@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
