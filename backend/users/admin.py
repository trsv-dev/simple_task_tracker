from django.contrib import admin
from django.utils.html import format_html

from users.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Класс администрирования профилей."""

    list_display = ('id', 'get_username', 'show_avatar',
                    'get_bio', 'telegram_username', 'telegram_chat_id',
                    'is_private')
    ordering = ('user_id__date_joined',)
    search_fields = ('user_id__username', 'telegram_username')
    list_per_page = 25

    def get_username(self, obj):
        return obj.user.username

    get_username.short_description = 'Пользователь'

    def get_bio(self, obj):
        return obj.bio[:50] + (
            '...' if len(obj.bio) > 50 else '')

    get_bio.short_description = 'Кратко о себе'

    def show_avatar(self, obj):
        if obj.user.profile.avatar:
            return format_html(
                '<img src="{}" style="max-width: 50px; max-height: 50px; '
                'object-fit: cover;" />', obj.user.profile.avatar.url
            )
        return 'Нет аватара'

    show_avatar.short_description = 'Аватар'
