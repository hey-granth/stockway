"""
Custom permission classes for role-based access control with object-level permissions.
"""

from rest_framework import permissions
import logging

logger = logging.getLogger(__name__)


class IsSuperAdmin(permissions.BasePermission):
    """
    Permission class to allow access only to super admins.
    """

    def has_permission(self, request, view):
        has_perm = (
            request.user
            and request.user.is_authenticated
            and (request.user.is_superuser or request.user.role == "ADMIN")
        )
        if not has_perm:
            self._log_permission_denied(request, "IsSuperAdmin")
        return has_perm

    def _log_permission_denied(self, request, permission_class):
        logger.warning(
            f"Permission denied - {permission_class}",
            extra={
                "user_id": request.user.id if request.user.is_authenticated else None,
                "path": request.path,
                "method": request.method,
            },
        )


class IsShopkeeper(permissions.BasePermission):
    """
    Permission class to allow access only to shopkeepers.
    """

    def has_permission(self, request, view):
        has_perm = (
            request.user
            and request.user.is_authenticated
            and request.user.role == "SHOPKEEPER"
        )
        if not has_perm:
            self._log_permission_denied(request, "IsShopkeeper")
        return has_perm

    def has_object_permission(self, request, view, obj):
        """Ensure shopkeeper can only access their own objects"""
        if hasattr(obj, "shopkeeper"):
            return obj.shopkeeper == request.user
        if hasattr(obj, "user"):
            return obj.user == request.user
        return True

    def _log_permission_denied(self, request, permission_class):
        logger.warning(
            f"Permission denied - {permission_class}",
            extra={
                "user_id": request.user.id if request.user.is_authenticated else None,
                "path": request.path,
                "method": request.method,
            },
        )


class IsWarehouseAdmin(permissions.BasePermission):
    """
    Permission class to allow access only to warehouse managers/admins.
    """

    def has_permission(self, request, view):
        has_perm = (
            request.user
            and request.user.is_authenticated
            and request.user.role == "WAREHOUSE_MANAGER"
        )
        if not has_perm:
            self._log_permission_denied(request, "IsWarehouseAdmin")
        return has_perm

    def has_object_permission(self, request, view, obj):
        """Ensure warehouse admin can only access their own warehouse objects"""
        # For Warehouse objects
        if hasattr(obj, "admin"):
            return obj.admin == request.user

        # For orders, check if warehouse belongs to admin
        if hasattr(obj, "warehouse"):
            return obj.warehouse.admin == request.user

        # For items, check warehouse ownership
        if hasattr(obj, "warehouse"):
            return obj.warehouse.admin == request.user

        # For riders, check if assigned to admin's warehouse
        if hasattr(obj, "user") and obj.user.role == "RIDER":
            # Check if rider is assigned to any of admin's warehouses
            warehouse_ids = request.user.warehouses.values_list("id", flat=True)
            return (
                obj.warehouse_id in warehouse_ids
                if hasattr(obj, "warehouse_id")
                else False
            )

        return True

    def _log_permission_denied(self, request, permission_class):
        logger.warning(
            f"Permission denied - {permission_class}",
            extra={
                "user_id": request.user.id if request.user.is_authenticated else None,
                "path": request.path,
                "method": request.method,
            },
        )


class IsWarehouseAdminOrSuperAdmin(permissions.BasePermission):
    """
    Permission class to allow access to warehouse admins or super admins.
    """

    def has_permission(self, request, view):
        has_perm = (
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_superuser
                or request.user.role == "ADMIN"
                or request.user.role == "WAREHOUSE_MANAGER"
            )
        )
        if not has_perm:
            self._log_permission_denied(request, "IsWarehouseAdminOrSuperAdmin")
        return has_perm

    def _log_permission_denied(self, request, permission_class):
        logger.warning(
            f"Permission denied - {permission_class}",
            extra={
                "user_id": request.user.id if request.user.is_authenticated else None,
                "path": request.path,
                "method": request.method,
            },
        )


class IsRider(permissions.BasePermission):
    """
    Permission class to allow access only to riders.
    """

    def has_permission(self, request, view):
        has_perm = (
            request.user
            and request.user.is_authenticated
            and request.user.role == "RIDER"
        )
        if not has_perm:
            self._log_permission_denied(request, "IsRider")
        return has_perm

    def has_object_permission(self, request, view, obj):
        """Ensure rider can only access their assigned orders"""
        # For delivery objects
        if hasattr(obj, "rider"):
            return obj.rider == request.user

        # For orders, check if assigned to this rider through delivery
        if hasattr(obj, "delivery"):
            return obj.delivery and obj.delivery.rider == request.user

        return True

    def _log_permission_denied(self, request, permission_class):
        logger.warning(
            f"Permission denied - {permission_class}",
            extra={
                "user_id": request.user.id if request.user.is_authenticated else None,
                "path": request.path,
                "method": request.method,
            },
        )
