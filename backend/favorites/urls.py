from django.urls import path

from favorites import views

app_name = 'favorites'

urlpatterns = [
    path(
        'add_to_favorites/<int:pk>/',
        views.add_to_favorites,
        name='add_to_favorites'
    ),
    path(
        'delete_from_favorites/<int:pk>/',
        views.delete_from_favorites,
        name='delete_from_favorites'
    ),
    path(
        '<str:user>/',
        views.get_favorites,
        name='favorites'
    )
]
