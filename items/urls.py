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

from payments.views import (
    create_payment,
    sync_payment_status,
    midtrans_notification,
    my_purchases,
)

app_name = 'items'

urlpatterns = [
    path('', show_marketplace, name='show_marketplace'),
    path('my-marketplace/', my_marketplace, name='my_marketplace'),
    path('api/items', get_items_json, name='get_items_json'),
    path('detail/<uuid:id>/', item_detail, name='item_detail'),

    # === ITEM CONFIGURATION === 
    path('like/<uuid:id>/', like_item, name='like_item'),
    path('dislike/<uuid:id>/', dislike_item, name='dislike_item'),
    path('like-ajax/<uuid:id>/', like_item_ajax, name='like_item_ajax'),
    path('dislike-ajax/<uuid:id>/', dislike_item_ajax, name='dislike_item_ajax'),
    path('add/', add_item, name='add_item'),
    path('edit/<uuid:id>/', edit_item, name='edit_item'),
    path('delete/<uuid:id>/', delete_item, name='delete_item'),

    # === PAYMENT CONFIGURATION === 
    path('pay/<uuid:id>/', create_payment, name='create_payment'),
    path('pay/status/<uuid:id>/', sync_payment_status, name='sync_payment_status'),
    path('midtrans/notification/', midtrans_notification, name='midtrans_notification'),
    path('my-purchases/', my_purchases, name='my_purchases'),
]