from django.db import models
from django.contrib.auth.models import User
from items.models import Item

import uuid

class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    text = models.TextField()
    
    liked_by = models.ManyToManyField(User, related_name='liked_comments', blank=True)
    disliked_by = models.ManyToManyField(User, related_name='disliked_comments', blank=True)

class Review(Comment):    
    item = models.ForeignKey(Item, related_name='reviews', on_delete=models.CASCADE)
    
class Reply(Comment):    
    to = models.ForeignKey(Comment, related_name='replies', on_delete=models.CASCADE)
    