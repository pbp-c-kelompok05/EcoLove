from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
<<<<<<< Updated upstream
from .views import login_user, register_user, logout_user, profile_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('login/', login_user, name='login'),
    path('register/', register_user, name='register'),
    path('logout/', logout_user, name='logout'),
    path('profile/', profile_view, name='profile'),
]
=======
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
>>>>>>> Stashed changes
