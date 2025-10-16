from rest_framework.permissions import BasePermission


class IsShopkeeper(BasePermission):
    """
    Allows access only to shopkeeper users.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'SHOPKEEPER')


class IsWarehouseAdmin(BasePermission):
    """
    Allows access only to warehouse admin users.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'WAREHOUSE_ADMIN')


class IsRider(BasePermission):
    """
    Allows access only to rider users.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'RIDER')


class IsSuperAdmin(BasePermission):
    """
    Allows access only to super admin users.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'SUPER_ADMIN')


class IsWarehouseAdminOrSuperAdmin(BasePermission):
    """
    Allows access only to warehouse admin or super admin users.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.role == 'WAREHOUSE_ADMIN' or request.user.role == 'SUPER_ADMIN'))
