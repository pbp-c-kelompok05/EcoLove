from django.utils.html import strip_tags
from rest_framework import serializers

from events.models import Education, Event


def _clean_required_text(value, field_label):
    cleaned = strip_tags(value).strip()
    if not cleaned:
        raise serializers.ValidationError(f"{field_label} cannot be empty.")
    return cleaned


class EventSerializer(serializers.ModelSerializer):
    """Serialize Event instances with role-aware private field filtering."""

    category_label = serializers.CharField(source="get_category_display", read_only=True)
    creator_name = serializers.CharField(source="creator.username", read_only=True)
    status_label = serializers.CharField(read_only=True)
    registration_open = serializers.BooleanField(read_only=True)
    registration_count = serializers.SerializerMethodField()
    is_registered = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "category",
            "category_label",
            "description",
            "starts_at",
            "ends_at",
            "location",
            "is_online",
            "organizer_contact",
            "meeting_link",
            "image",
            "creator_name",
            "status_label",
            "registration_open",
            "registration_count",
            "is_registered",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_title(self, value):
        return _clean_required_text(value, "Title")

    def validate_description(self, value):
        return _clean_required_text(value, "Description")

    def validate_location(self, value):
        return _clean_required_text(value, "Location")

    def validate_organizer_contact(self, value):
        return strip_tags(value).strip()

    def validate(self, attrs):
        starts_at = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends_at = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        if starts_at and ends_at and ends_at < starts_at:
            raise serializers.ValidationError(
                {"ends_at": "Waktu selesai tidak boleh sebelum waktu mulai."}
            )
        return attrs

    def get_registration_count(self, obj):
        return obj.registrations.count()

    def get_is_registered(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return obj.registrations.filter(user=request.user).exists()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            data.pop("organizer_contact", None)
            data.pop("meeting_link", None)
        else:
            data["meeting_link"] = instance.safe_meeting_link
        return data


class EducationSerializer(serializers.ModelSerializer):
    """Serialize Education articles with sanitized text validation."""

    category_label = serializers.CharField(source="get_category_display", read_only=True)
    author_name = serializers.CharField(source="author.username", read_only=True)

    class Meta:
        model = Education
        fields = [
            "id",
            "title",
            "category",
            "category_label",
            "summary",
            "body",
            "image",
            "author_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_title(self, value):
        return _clean_required_text(value, "Title")

    def validate_summary(self, value):
        return _clean_required_text(value, "Summary")

    def validate_body(self, value):
        return _clean_required_text(value, "Body")
