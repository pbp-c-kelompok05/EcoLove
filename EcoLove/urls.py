from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from items import views as item_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('marketplace/', include('items.urls')),  
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('events/', item_views.show_events, name='show_events'),
    path('', include('users.urls')),             
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)