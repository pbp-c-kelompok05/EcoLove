from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from events.models import Education, Event, EventComment, EventRegistration
from events.permissions import IsSuperuserOrReadOnly
from events.serializers import (
    EducationSerializer,
    EventCommentSerializer,
    EventSerializer,
)


def _detail_response(request, instance, serializer_class):
    if request.method in ("GET", "HEAD"):
        serializer = serializer_class(instance, context={"request": request})
        return Response(serializer.data)

    if request.method == "DELETE":
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = serializer_class(
        instance,
        data=request.data,
        partial=request.method == "PATCH",
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["GET", "HEAD", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsSuperuserOrReadOnly])
def event_list(request):
    """List or search events, or create a new event (superuser only)."""
    if request.method in ("GET", "HEAD"):
        events = Event.objects.select_related("creator").prefetch_related("registrations")
        query = (
            request.query_params.get("q")
            or request.query_params.get("title")
            or ""
        ).strip()[:200]
        if query:
            events = events.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(location__icontains=query)
            )
        category = request.query_params.get("category", "").strip()
        if category:
            events = events.filter(category=category)
        status_filter = request.query_params.get("status", "").strip()
        now = timezone.now()
        if status_filter == "upcoming":
            events = events.filter(starts_at__gt=now)
        elif status_filter == "ongoing":
            events = events.filter(starts_at__lte=now, ends_at__gte=now)
        elif status_filter == "finished":
            events = events.filter(ends_at__lt=now)

        serializer = EventSerializer(events, many=True, context={"request": request})
        return Response(serializer.data)

    serializer = EventSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save(creator=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "HEAD", "PUT", "PATCH", "DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsSuperuserOrReadOnly])
def event_detail(request, event_id):
    """Retrieve, update, or delete a single event."""
    event = get_object_or_404(
        Event.objects.select_related("creator").prefetch_related("registrations"),
        pk=event_id,
    )
    return _detail_response(request, event, EventSerializer)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def event_participate(request, event_id):
    """Toggle authenticated user's registration for an upcoming event."""
    with transaction.atomic():
        event = get_object_or_404(Event.objects.select_for_update(), pk=event_id)
        registrations = event.registrations.filter(user=request.user)
        if registrations.exists():
            registrations.delete()
        elif not event.registration_open:
            return Response(
                {"detail": "Pendaftaran ditutup karena event sudah dimulai atau selesai."},
                status=status.HTTP_409_CONFLICT,
            )
        else:
            EventRegistration.objects.get_or_create(event=event, user=request.user)

    serializer = EventSerializer(event, context={"request": request})
    return Response(serializer.data)


@api_view(["GET", "HEAD", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticatedOrReadOnly])
def event_comment_list(request, event_id):
    """List comments for an event, or post a new comment (authenticated users)."""
    event = get_object_or_404(Event, pk=event_id)
    if request.method in ("GET", "HEAD"):
        comments = event.comments.select_related("user")
        serializer = EventCommentSerializer(
            comments, many=True, context={"request": request}
        )
        return Response(serializer.data)

    serializer = EventCommentSerializer(
        data=request.data, context={"request": request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save(event=event, user=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def event_comment_detail(request, comment_id):
    """Delete a comment (comment author or superuser only)."""
    comment = get_object_or_404(EventComment, pk=comment_id)
    if comment.user_id != request.user.pk and not request.user.is_superuser:
        return Response(
            {"detail": "Anda hanya boleh menghapus komentar sendiri."},
            status=status.HTTP_403_FORBIDDEN,
        )
    comment.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET", "HEAD", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsSuperuserOrReadOnly])
def education_list(request):
    """List or search education articles, or create a new article (superuser only)."""
    if request.method in ("GET", "HEAD"):
        articles = Education.objects.select_related("author")
        query = (
            request.query_params.get("q")
            or request.query_params.get("title")
            or ""
        ).strip()[:200]
        if query:
            articles = articles.filter(
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(body__icontains=query)
            )
        category = request.query_params.get("category", "").strip()
        if category:
            articles = articles.filter(category=category)

        serializer = EducationSerializer(articles, many=True, context={"request": request})
        return Response(serializer.data)

    serializer = EducationSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save(author=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "HEAD", "PUT", "PATCH", "DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsSuperuserOrReadOnly])
def education_detail(request, education_id):
    """Retrieve, update, or delete a single education article."""
    article = get_object_or_404(
        Education.objects.select_related("author"),
        pk=education_id,
    )
    return _detail_response(request, article, EducationSerializer)
