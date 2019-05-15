from rest_framework import permissions
from . import models as app_models
from django.utils import timezone


class BasePermission(permissions.BasePermission):
    LOGIN_REFRESH_INTERVAL = 60 * 30     # seconds

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            user = request.user
            now = timezone.now()
            if user.last_login is None or \
                    (now - user.last_login).seconds >= self.LOGIN_REFRESH_INTERVAL:
                user.last_login = now
                user.save()


class IsLogin(BasePermission):
    def has_permission(self, request, view):
        super().has_permission(request, view)
        user = request.user
        return user is not None and user.is_authenticated


class IsStaff(BasePermission):
    def has_permission(self, request, view):
        super().has_permission(request, view)
        user = request.user
        return user is not None and user.is_authenticated and user.is_staff


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        super().has_permission(request, view)
        user = request.user
        return user is not None and user.is_authenticated and \
               hasattr(user, 'student') and getattr(user, 'student') is not None
