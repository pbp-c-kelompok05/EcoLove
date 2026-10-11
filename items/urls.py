from django.urls import path
from . import views

app_name = 'items'

urlpatterns = [
    path('', views.show_home, name='home'),
    path('marketplace/', views.show_marketplace, name='show_marketplace'),
    path('events/', views.show_events, name='show_events'),
    path('add/', views.add_item, name='add_item'),
    path('<int:id>/', views.item_detail, name='item_detail'),
    path('like/<int:id>/', views.like_item, name='like_item'),
    path('dislike/<int:id>/', views.dislike_item, name='dislike_item'),
]