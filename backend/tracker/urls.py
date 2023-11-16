from django.urls import path

from tracker import views

app_name = 'tracker'

urlpatterns = [
    path('', views.index, name='index'),
    path('profile/<str:user>/', views.profile, name='profile'),
    path('detail/<int:pk>/', views.task_detail, name='detail'),
    path('create/', views.create_task, name='create'),
    path('edit/<int:pk>/', views.edit_task, name='edit'),
    path('delete/<int:pk>/', views.delete_task, name='delete'),
    path(
        'detail/<int:task_pk>/comment/',
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
    path(
        'tasks/<int:pk>/mark_as_done/',
        views.mark_as_done,
        name='mark_as_done'
    ),
    path(
        'tasks/<int:pk>/mark_as_undone',
        views.mark_as_undone,
        name='mark_as_undone'),
]
