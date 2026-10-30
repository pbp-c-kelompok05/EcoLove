from django.db import models
from django.contrib.auth.models import User

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    recipient_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    full_address = models.TextField()
    city_province_postal = models.CharField(max_length=200)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.recipient_name} - {self.city_province_postal}"