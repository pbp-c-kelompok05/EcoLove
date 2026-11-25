from rest_framework import serializers
from .models import Item

class ItemSerializer(serializers.ModelSerializer):
    seller = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Item
        fields = ['id', 'name', 'price', 'description', 'category', 'image', 'seller']