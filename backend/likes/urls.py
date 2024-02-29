from django.urls import path

from likes import views

app_name = 'likes'

urlpatterns = [
    path('add_like/<int:pk>/', views.add_like, name='add_like'),
    path('delete_like/<int:pk>/', views.delete_like, name='delete_like')
]
