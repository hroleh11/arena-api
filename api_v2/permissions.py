from rest_framework import permissions


class IsNewsOwner(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        return bool(hasattr(user, 'profile') and obj.profile == getattr(user, 'profile', None))
