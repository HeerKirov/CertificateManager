from rest_framework import permissions
from . import models as app_models


class IsLogin(permissions.BasePermission):
    def has_permission(self, request, view):
        super().has_permission(request, view)
        user = request.user
        return user is not None and user.is_authenticated


class IsStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        super().has_permission(request, view)
        user = request.user
        return user is not None and user.is_authenticated and user.is_staff


class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        super().has_permission(request, view)
        user = request.user
        return user is not None and user.is_authenticated and \
               hasattr(user, 'student') and getattr(user, 'student') is not None
