from django.urls import path
from items.views import show_marketplace, item_detail, like_item, dislike_item, add_item, edit_item, delete_item

app_name = 'items'

urlpatterns = [
    path('', show_marketplace, name='show_marketplace'),
    path('detail/<int:id>/', item_detail, name='item_detail'),
    path('like/<int:id>/', like_item, name='like_item'),
    path('dislike/<int:id>/', dislike_item, name='dislike_item'),
    path('add/', add_item, name='add_item'),
    path('edit/<int:id>/', edit_item, name='edit_item'),
    path('delete/<int:id>/', delete_item, name='delete_item'),
]