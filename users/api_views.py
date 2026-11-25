
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .models import Address
from .serializers import (
    RegisterSerializer,
    UserProfileSerializer,
    AddressSerializer,
)


# REGISTER
@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    serializer = RegisterSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'message': 'Account created successfully.',
            'token': token.key,
            'user': UserProfileSerializer(user).data,
        }, status=status.HTTP_201_CREATED)

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


# LOGIN
@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    username = request.data.get('username', '')
    password = request.data.get('password', '')

    user = authenticate(
        request,
        username=username,
        password=password
    )

    if user is None:
        return Response({
            'message': 'Invalid username or password.'
        }, status=status.HTTP_401_UNAUTHORIZED)

    token, created = Token.objects.get_or_create(user=user)

    return Response({
        'message': 'Login successful.',
        'token': token.key,
        'user': UserProfileSerializer(user).data,
    }, status=status.HTTP_200_OK)


# LOGOUT
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def logout_api(request):
    Token.objects.filter(user=request.user).delete()

    return Response({
        'message': 'Logout successful.'
    }, status=status.HTTP_200_OK)


# PROFILE
@api_view(['GET', 'PATCH'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def profile_api(request):

    if request.method == 'GET':
        serializer = UserProfileSerializer(request.user)

        return Response(serializer.data)

    serializer = UserProfileSerializer(
        request.user,
        data=request.data,
        partial=True
    )

    if serializer.is_valid():
        serializer.save()

        return Response({
            'message': 'Profile updated successfully.',
            'user': serializer.data,
        })

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


# ADDRESS LIST AND CREATE
@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def address_list_api(request):

    if request.method == 'GET':
        addresses = Address.objects.filter(
            user=request.user
        ).order_by('-is_primary', '-id')

        serializer = AddressSerializer(
            addresses,
            many=True
        )

        return Response(serializer.data)

    serializer = AddressSerializer(data=request.data)

    if serializer.is_valid():
        if serializer.validated_data.get('is_primary', False):
            Address.objects.filter(
                user=request.user,
                is_primary=True
            ).update(is_primary=False)

        serializer.save(user=request.user)

        return Response({
            'message': 'Address added successfully.',
            'address': serializer.data,
        }, status=status.HTTP_201_CREATED)

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


# ADDRESS DELETE
@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def address_delete_api(request, address_id):

    try:
        address = Address.objects.get(
            id=address_id,
            user=request.user
        )
    except Address.DoesNotExist:
        return Response({
            'message': 'Address not found.'
        }, status=status.HTTP_404_NOT_FOUND)

    address.delete()

    return Response(
        status=status.HTTP_204_NO_CONTENT
    )
