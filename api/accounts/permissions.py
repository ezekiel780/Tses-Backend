from django.conf import settings
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied


class AllUsers(BasePermission):
    """
    Permission class that allows any authenticated user to access the resource.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            raise PermissionDenied('Authentication required.')
        return True


class IsOwner(BasePermission):
    """
    Permission class that only allows the owner of an object to access it.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsAdminUser(BasePermission):
    """
    Permission class that only allows admin users to access the resource.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            raise PermissionDenied('Authentication required.')
        if not user.is_staff:
            raise PermissionDenied('Admin access required.')
        return True


class IsSuperUser(BasePermission):
    """
    Permission class that only allows superuser to access the resource.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            raise PermissionDenied('Authentication required.')
        if not user.is_superuser:
            raise PermissionDenied('Superuser access required.')
        return True
