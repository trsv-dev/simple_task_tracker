from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('tracker/', include('tracker.urls')),
    # path('', include('tracker.urls')),
    path('admin/', admin.site.urls),
]
