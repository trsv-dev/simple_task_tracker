from django.urls import path

from tracker import views

urlpatterns = [
    path('', views.test, name='test'),
]
