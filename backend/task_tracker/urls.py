from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from task_tracker import settings

urlpatterns = [
    path('profile/', include('users.urls')),

    path('', include('tracker.urls')),
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('comments/', include('comments.urls')),
    path('favorites/', include('favorites.urls')),
    path('tags/', include('tags.urls')),
    path('likes/', include('likes.urls')),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )

    urlpatterns += (path('__debug__/', include(debug_toolbar.urls)),)
