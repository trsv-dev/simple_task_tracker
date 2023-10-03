from django.urls import path

from tracker import views

app_name = 'tracker'

urlpatterns = [
    path('', views.index, name='index'),
    path('create/', views.create_task, name='create'),
    path('edit/<int:pk>/', views.edit_task, name='edit'),
    path('delete/<int:pk>/', views.delete_task, name='delete'),
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
