from django.contrib import admin

from tracker.models import Task

admin.site.site_header = "Трекер задач"
admin.site.site_title = "Панель администрирования"
admin.site.index_title = "Добро пожаловать в трекер задач"


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'priority',
                    'status', 'created', 'deadline')
    ordering = ('created',)
