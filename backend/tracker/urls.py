from django.urls import path

from tracker import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create/', views.create_task, name='create'),
    path('edit/<int:pk>/', views.edit_task, name='edit'),
    path('delete/<int:pk>/', views.delete_task, name='delete'),
]
