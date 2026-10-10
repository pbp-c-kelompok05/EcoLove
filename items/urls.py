from django.urls import path
from items.views import show_marketplace, item_detail, like_item, dislike_item, add_item

app_name = 'items'

urlpatterns = [
    path('', show_marketplace, name='show_marketplace'),
    path('detail/<int:id>/', item_detail, name='item_detail'),
    path('like/<int:id>/', like_item, name='like_item'),
    path('dislike/<int:id>/', dislike_item, name='dislike_item'),
    path('add/', add_item, name='add_item'),
]