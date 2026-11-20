from django.contrib.auth.models import User
from django.utils.html import strip_tags, conditional_escape
from rest_framework import serializers
from rest_framework.fields import UUIDField

from .models import Review

from items.models import Item


class ReviewSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    dislike_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_disliked = serializers.SerializerMethodField()
    is_deletable = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id", "owner", "user", "item",
            "text", "rating",
            "like_count", "dislike_count",
            "is_liked", "is_disliked",
            "is_deletable", "is_owner",
        ]
        read_only_fields = [
            "id", "owner",
            "like_count", "dislike_count",
            "is_liked", "is_disliked",
            "is_deletable", "is_owner",
        ]

    def validate_text(self, value):
        if not value:
            raise serializers.ValidationError("Review text cannot be empty.")
        return strip_tags(conditional_escape(value))

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1-5.")
        return value

    def get_owner(self, obj):
        return obj.user.username

    def get_like_count(self, obj):
        return obj.liked_by.count()

    def get_dislike_count(self, obj):
        return obj.disliked_by.count()

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return request.user in obj.liked_by.all()

    def get_is_disliked(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return request.user in obj.disliked_by.all()

    def get_is_deletable(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return request.user.is_staff or request.user == obj.user

    def get_is_owner(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return request.user == obj.user