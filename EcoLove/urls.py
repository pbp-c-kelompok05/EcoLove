from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.core.files.storage import default_storage
from pathlib import Path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('', include('users.urls')),
    path('events/', include('events.urls')),
    path('marketplace/', include('items.urls')),
    path('reviews/', include('reviews.urls'))
]

# This block is required to serve images locally
if settings.DEBUG:
    if settings.MEDIA_ROOT:
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    else:
        # Legacy FileSystemStorage uses the working directory. Serve upload
        # folders only: a catch-all MEDIA_URL='/' would expose project files.
        for folder in ('item_images', 'event_images', 'education_images'):
            urlpatterns += static(
                f'{settings.MEDIA_URL}{folder}/',
                document_root=Path(default_storage.location) / folder,
            )
