from django.urls import path
from payments.views import (
    create_payment,
    sync_payment_status,
    midtrans_notification,
    my_purchases,
    cancel_order,
    
)

app_name = 'payments'

urlpatterns = [
    path('pay/<uuid:id>/', create_payment, name='create_payment'),
    path('pay/status/<uuid:id>/', sync_payment_status, name='sync_payment_status'),
    path('midtrans/notification/', midtrans_notification, name='midtrans_notification'),
    path('my-purchases/', my_purchases, name='my_purchases'),
    path('cancel/<uuid:id>/', cancel_order, name='cancel_order'),
]