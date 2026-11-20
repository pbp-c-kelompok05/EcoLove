from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes,
)

from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Review
from .permissions import WriteReviewPermission
from .serializers import ReviewSerializer

from items.models import Item


@api_view(["GET", "HEAD", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([WriteReviewPermission])
def review_list(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if request.method in ("GET", "HEAD"):
        reviews = Review.objects.filter(item=item) \
            .prefetch_related("liked_by", "disliked_by")
            
        rating = request.query_params.get("rating", "").strip()
        if rating:
            reviews = reviews.filter(rating=rating)
        serializer = ReviewSerializer(
            reviews, many=True, context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    if Review.objects.filter(item=item, user=request.user).exists():
        return Response(status=status.HTTP_409_CONFLICT)

    data = request.data.copy()
    data["user"] = request.user.pk
    data["item"] = item.pk
    serializer = ReviewSerializer(data=data, context={"request": request})
    serializer.is_valid()
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(["GET", "HEAD", "PUT", "PATCH", "DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes([WriteReviewPermission])
def review_detail(request, review_id):
    review = get_object_or_404(
        Review.objects.prefetch_related("liked_by", "disliked_by"), pk=review_id,
    )
    if request.method in ("GET", "HEAD"):
        serializer = ReviewSerializer(review, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == "DELETE":
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = ReviewSerializer(
        review, data=request.data, partial=request.method == "PATCH",
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)

@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def review_like(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    if review.liked_by.filter(pk=request.user.pk).exists():
        review.liked_by.remove(request.user)
    else:
        review.liked_by.add(request.user)
        review.disliked_by.remove(request.user)
    serializer = ReviewSerializer(review, context={"request": request})
    return Response(serializer.data)

@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def review_dislike(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    if review.disliked_by.filter(pk=request.user.pk).exists():
        review.disliked_by.remove(request.user)
    else:
        review.disliked_by.add(request.user)
        review.liked_by.remove(request.user)
    serializer = ReviewSerializer(review, context={"request": request})
    return Response(serializer.data)