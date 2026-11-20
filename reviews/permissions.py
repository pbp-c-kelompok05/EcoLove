from rest_framework.permissions import BasePermission, SAFE_METHODS


class WriteReviewPermission(BasePermission):
    message = "Only the owner and admin can change review data."

    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
            or request.user.is_superuser
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or request.user.is_superuser
            or obj.user == request.user
        )