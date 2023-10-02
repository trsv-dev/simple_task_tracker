from django.contrib import admin
from django.contrib.auth import views
from django.urls import include, path

urlpatterns = [
    path('', include('tracker.urls')),
    path('admin/', admin.site.urls),
    path('auth/', include('django.contrib.auth.urls')),
]
