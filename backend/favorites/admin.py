from django.contrib import admin

from favorites.models import Favorites


@admin.register(Favorites)
class FavoritesAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'added_time')
    ordering = ('-added_time',)
    search_fields = ('task__title', 'user__username')
