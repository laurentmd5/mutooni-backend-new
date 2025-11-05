from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """Accès réservé aux utilisateurs rôle = admin."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"

class IsVendor(permissions.BasePermission):
    """Accès réservé aux vendeurs (ou admins)."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ("vendor", "admin")
        )

class IsStaff(permissions.BasePermission):
    """Accès réservé au staff (ou admins)."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in ("staff", "admin")
        )
