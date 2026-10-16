from django.urls import path
from items.views import (
    show_marketplace,
    my_marketplace,
    item_detail,
    like_item,
    like_item_ajax,
    dislike_item,
    dislike_item_ajax,
    add_item,
    edit_item,
    delete_item,
    get_items_json,
)

app_name = 'items'

urlpatterns = [
    path('', show_marketplace, name='show_marketplace'),
    path('my-marketplace/', my_marketplace, name='my_marketplace'),
    path('api/items', get_items_json, name='get_items_json'),
    path('detail/<int:id>/', item_detail, name='item_detail'),

    # === ITEM CONFIGURATION === 
    path('like/<int:id>/', like_item, name='like_item'),
    path('dislike/<int:id>/', dislike_item, name='dislike_item'),
    path('like-ajax/<int:id>/', like_item_ajax, name='like_item_ajax'),
    path('dislike-ajax/<int:id>/', dislike_item_ajax, name='dislike_item_ajax'),
    path('add/', add_item, name='add_item'),
    path('edit/<int:id>/', edit_item, name='edit_item'),
    path('delete/<int:id>/', delete_item, name='delete_item'),
]