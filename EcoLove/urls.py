from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from .views import login_user, register_user, logout_user, profile_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('login/', login_user, name='login'),
    path('register/', register_user, name='register'),
    path('logout/', logout_user, name='logout'),
    path('profile/', profile_view, name='profile'),
]