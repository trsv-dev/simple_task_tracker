from django.contrib import admin

from tracker.models import Task, Tags, TaskTag

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

    list_display = ('author', 'title', 'description', 'show_tags', 'priority',
                    'status', 'assigned_to', 'created', 'deadline', 'is_done',
                    'done_by', 'done_by_time')
    ordering = ('created',)
    inlines = (TagsInLine,)


@admin.register(TaskTag)
class TaskTagsAdmin(admin.ModelAdmin):
    list_display = ('task', 'tag')


@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
