from rest_framework import permissions


class IsWarehouseAdmin(permissions.BasePermission):
    """Permission for warehouse administrators"""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["WAREHOUSE_MANAGER", "ADMIN"]
        )

    def has_object_permission(self, request, view, obj):
        # Admin can access all warehouses
        if request.user.role == "ADMIN":
            return True

        # Check if user is the warehouse admin
        if hasattr(obj, "admin"):
            return obj.admin == request.user

        # For nested resources (e.g., inventory items)
        if hasattr(obj, "warehouse"):
            return obj.warehouse.admin == request.user

        return False


class IsWarehouseAdminOrReadOnly(permissions.BasePermission):
    """Allow read access to all, write access to warehouse admin only"""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["WAREHOUSE_MANAGER", "ADMIN"]
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Admin can modify all warehouses
        if request.user.role == "ADMIN":
            return True

        # Check if user is the warehouse admin
        if hasattr(obj, "admin"):
            return obj.admin == request.user

        if hasattr(obj, "warehouse"):
            return obj.warehouse.admin == request.user

        return False


class IsWarehouseOrRider(permissions.BasePermission):
    """Permission for warehouse admin or assigned rider"""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["WAREHOUSE_MANAGER", "RIDER", "ADMIN"]
        )

    def has_object_permission(self, request, view, obj):
        # Admin can access all
        if request.user.role == "ADMIN":
            return True

        # Warehouse admin can access their orders
        if hasattr(obj, "warehouse") and obj.warehouse.admin == request.user:
            return True

        # Rider can access assigned orders (read-only for most fields)
        if hasattr(obj, "rider") and obj.rider and obj.rider.user == request.user:
            return True

        return False

