from django.db import models
from django.contrib.auth.models import User

import uuid

class Item(models.Model):
    CATEGORY_CHOICES = [
        ('CLOTHES', 'Clothes'),
        ('ELECTRONICS', 'Electronics'),
        ('FURNITURE', 'Furniture'),
        ('OTHERS', 'Others'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    price = models.IntegerField() 
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OTHERS')
    
    # 'Pillow' buat upload image
    image = models.ImageField(upload_to='item_images/', null=True, blank=True)
    
    # Interaction fields:
    liked_by = models.ManyToManyField(User, related_name='liked_items', blank=True)
    disliked_by = models.ManyToManyField(User, related_name='disliked_items', blank=True)

    def __str__(self):
        return self.name

    @property 
    def is_sold(self):
        return self.order_set.filter(status='PAID').exists()

# models.py
class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'), ('PAID', 'Paid'),
        ('FAILED', 'Failed'), ('EXPIRED', 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # sent to Midtrans as order_id
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    snap_token = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)