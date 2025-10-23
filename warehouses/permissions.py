from rest_framework.permissions import BasePermission
from configs.permissions import IsWarehouseAdminOrSuperAdmin, IsSuperAdmin
from .models import Warehouse


class IsWarehouseOwnerOrSuperAdmin(BasePermission):
    """
    Object-level permission to only allow the warehouse's admin to view/update it,
    unless the user is a SUPER_ADMIN.
    """

    def has_object_permission(self, request, view, obj: Warehouse):
        if not request.user or not request.user.is_authenticated:
            return False
        if IsSuperAdmin().has_permission(request, view):
            return True
        # Only owner admin can access
        return getattr(obj, "admin_id", None) == request.user.id


class HasWarehouseRole(BasePermission):
    """
    Gate all warehouse endpoints to warehouse admins or super admins.
    """

    def has_permission(self, request, view):
        return IsWarehouseAdminOrSuperAdmin().has_permission(request, view)
