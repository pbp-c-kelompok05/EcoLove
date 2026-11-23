from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSuperuserOrReadOnly(BasePermission):
    """Allow read-only access to anyone, and write access only to superusers."""

    message = "Only superusers can modify this content."

    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or bool(request.user and request.user.is_superuser)
        )
