from rest_framework.permissions import BasePermission


class IsShopkeeper(BasePermission):
    """
    Permission class to check if user is a shopkeeper
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'SHOPKEEPER'
        )


class IsRider(BasePermission):
    """
    Permission class to check if user is a rider
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'RIDER'
        )


class IsWarehouseManager(BasePermission):
    """
    Permission class to check if user is a warehouse manager
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'WAREHOUSE_MANAGER'
        )


class IsAdmin(BasePermission):
    """
    Permission class to check if user is an admin
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'ADMIN'
        )

