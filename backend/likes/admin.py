from django.contrib import admin

from likes.models import Likes


@admin.register(Likes)
class LikesAdmin(admin.ModelAdmin):
    list_display = ('get_text', 'user', 'added_time')
    ordering = ('-added_time',)
    search_fields = ('comment__text', 'user__username')

    def get_text(self, obj):
        """Обрезаем длинные комментарии."""

        return obj.comment.text[:50] + (
            '...' if len(obj.comment.text) > 50 else '')

    get_text.short_description = 'текст'
