from django.db import models
from django.contrib.auth.models import User

class Item(models.Model):
    CATEGORY_CHOICES = [
        ('CLOTHES', 'Clothes'),
        ('ELECTRONICS', 'Electronics'),
        ('FURNITURE', 'Furniture'),
        ('OTHERS', 'Others'),
    ]

    name = models.CharField(max_length=255)
    price = models.IntegerField() 
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OTHERS')
    
    # 'Pillow' library installed for image uploading
    image = models.ImageField(upload_to='item_images/', null=True, blank=True)
    
    # Interaction fields:
    liked_by = models.ManyToManyField(User, related_name='liked_items', blank=True)
    disliked_by = models.ManyToManyField(User, related_name='disliked_items', blank=True)

    def __str__(self):
        return self.name

class ImagesField(models.ImageField):
    description = "A field for images with foreign key pointed to items."

    def __init__(self, *args, **kwargs):
        kwargs["item"] = models.ForeignKey(Item, related_name="images", on_delete=models.CASCADE)
        super().__init__(*args, **kwargs)