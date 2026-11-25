
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Address


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'password',
        ]
        read_only_fields = ['id']

    def validate_email(self, value):
        value = value.strip()

        if not value.lower().endswith('@gmail.com'):
            raise serializers.ValidationError(
                "Email must use a valid Gmail address."
            )

        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "Email is already taken."
            )

        return value

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "Username is already taken."
            )

        return value

    def validate_password(self, value):
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least 1 uppercase letter."
            )

        if not any(not char.isalpha() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least 1 number or special character."
            )

        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
        ]
        read_only_fields = ['id', 'username']


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id',
            'recipient_name',
            'phone_number',
            'full_address',
            'city_province_postal',
            'is_primary',
        ]
        read_only_fields = ['id']
