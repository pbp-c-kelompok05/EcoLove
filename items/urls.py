from django.urls import path
from items.views import (
    show_marketplace,
    item_detail,
    like_item,
    like_item_ajax,
    dislike_item,
    dislike_item_ajax,
    add_item,
    get_items_json
)

app_name = 'items'

urlpatterns = [
    path('', show_marketplace, name='show_marketplace'),
    path('api/items', get_items_json, name='get_items_json'),
    path('detail/<int:id>/', item_detail, name='item_detail'),
    path('like/<int:id>/', like_item_ajax, name='like_item'),
    path('dislike/<int:id>/', dislike_item_ajax, name='dislike_item'),
    path('add/', add_item, name='add_item'),
]