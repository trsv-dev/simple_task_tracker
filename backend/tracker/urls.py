from django.urls import path

from tracker import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create/', views.create_task, name='create'),
]
