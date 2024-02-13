from django.contrib import admin

from comments.models import Comment, CommentImage


class CommentImageInline(admin.TabularInline):
    model = CommentImage
    extra = 1


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_task', 'author', 'get_text', 'created')
    ordering = ('created',)
    search_fields = ('task__author__username', 'task__author__email', 'text')

    inlines = (CommentImageInline,)

    def get_text(self, obj):
        """Обрезаем длинные комментарии."""

        return obj.text[:50] + ('...' if len(obj.text) > 50 else '')

    def get_task(self, obj):
        """Обрезаем длинные заголовки задачи."""

        return (obj.task.title[:50] +
                ('...' if len(obj.task.title) > 50 else ''))

    get_text.short_description = 'текст'
    get_task.short_description = 'задача'