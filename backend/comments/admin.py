from django.contrib import admin
from django.db.models import Count

from comments.models import Comment, CommentImage


class CommentImageInline(admin.TabularInline):
    model = CommentImage
    extra = 1


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_task', 'author', 'get_likes_count', 'get_text',
                    'created')
    ordering = ('created',)
    search_fields = ('task__author__username', 'task__author__email', 'text')

    inlines = (CommentImageInline,)

    def get_text(self, obj):
        """Обрезаем длинные комментарии."""

        return obj.text[:50] + ('...' if len(obj.text) > 50 else '')

    get_text.short_description = 'текст'

    def get_task(self, obj):
        """Обрезаем длинные заголовки задачи."""

        return (obj.task.title[:50] +
                ('...' if len(obj.task.title) > 50 else ''))

    get_task.short_description = 'задача'

    def get_queryset(self, request):
        """
        Добавляем аннотацию для подсчета количества лайков для комментария.
        """

        return super().get_queryset(request).annotate(
            likes_count=Count('likes'))

    def get_likes_count(self, obj):
        """Выводим количество лайков."""

        return obj.likes_count

    get_likes_count.short_description = 'количество лайков'
