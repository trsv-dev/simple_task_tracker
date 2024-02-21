from django.urls import path

from comments import views

app_name = 'comments'

urlpatterns = [
    # path(
    #     'detail/<int:task_pk>/comment/',
    #     views.create_comment,
    #     name='create_comment'
    # ),
    path(
        'detail/<int:task_pk>/',
        views.create_comment,
        name='create_comment'
    ),
    path(
        'edit_comment/<int:pk>/',
        views.edit_comment,
        name='edit_comment'),
    path(
        'delete_comment/<int:pk>/',
        views.delete_comment,
        name='delete_comment'),
]
