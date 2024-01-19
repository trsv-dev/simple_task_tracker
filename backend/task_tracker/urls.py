from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from task_tracker import settings

urlpatterns = [
    path('', include('tracker.urls')),
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('auth/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )