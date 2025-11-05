# backend/views/permissions.py
from rest_framework.permissions import BasePermission

class IsAuthenticatedWithJWT(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
