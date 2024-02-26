from django.urls import path

from tags import views

app_name = 'tags'

urlpatterns = [
    path('<str:tag_name>/', views.filter_by_tag, name='by_tag')
]
