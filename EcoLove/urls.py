from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from .views import login_user, register_user, logout_user, profile_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('marketplace/', include('items.urls')),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('login/', login_user, name='login'),
    path('register/', register_user, name='register'),
    path('logout/', logout_user, name='logout'),
    path('profile/', profile_view, name='profile'),
]

# This block is required to serve images locally
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)