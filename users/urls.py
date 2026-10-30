from django.urls import path
from .views import login_user, register_user, logout_user, profile_view, add_address, delete_address
urlpatterns = [
    path('login/', login_user, name='login'),
    path('register/', register_user, name='register'),
    path('logout/', logout_user, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('profile/add-address/', add_address, name='add_address'),
    path('profile/delete-address/<int:address_id>/', delete_address, name='delete_address'),
]