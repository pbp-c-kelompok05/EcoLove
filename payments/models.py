from django.db import models
from django.contrib.auth.models import User

from items.models import Item

import uuid

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'), ('PAID', 'Paid'),
        ('FAILED', 'Failed'), ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # sent to Midtrans as order_id
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    snap_token = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    shipping_address = models.TextField(blank=True, default='')
    note = models.CharField(max_length=255, blank=True, default='')
