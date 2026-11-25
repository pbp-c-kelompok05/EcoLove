
from django.urls import path

from . import api_views

app_name = 'users_api'

urlpatterns = [
    # Authentication
    path('register/', api_views.register_api, name='register'),
    path('login/', api_views.login_api, name='login'),
    path('logout/', api_views.logout_api, name='logout'),

    # User Profile
    path('profile/', api_views.profile_api, name='profile'),

    # User Addresses
    path('addresses/', api_views.address_list_api, name='address-list'),
    path(
        'addresses/<int:address_id>/',
        api_views.address_delete_api,
        name='address-delete'
    ),
]
