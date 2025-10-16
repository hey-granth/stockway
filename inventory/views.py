from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.shortcuts import get_object_or_404

from .models import Item
from .serializers import ItemSerializer
from warehouses.models import Warehouse
from warehouses.permissions import HasWarehouseRole, IsWarehouseOwnerOrSuperAdmin
from configs.permissions import IsSuperAdmin


class WarehouseScopedMixin:
    """
    Mixin to retrieve a warehouse from URL kwargs and enforce object-level permission:
    - Only the warehouse's admin can manage its items, unless the user is SUPER_ADMIN.
    """

    lookup_warehouse_url_kwarg = "warehouse_id"

    def get_warehouse(self) -> Warehouse:
        warehouse_id = self.kwargs.get(self.lookup_warehouse_url_kwarg)
        warehouse = get_object_or_404(Warehouse, pk=warehouse_id)
        # Object-level permission check using existing permission helper
        request = self.request
        view = self
        if not IsSuperAdmin().has_permission(request, view):
            if not IsWarehouseOwnerOrSuperAdmin().has_object_permission(request, view, warehouse):
                # Hide existence
                raise NotFound()
        return warehouse


class ItemListCreateView(WarehouseScopedMixin, generics.ListCreateAPIView):
    """
    List and create inventory items for a given warehouse.
    URL must include warehouse_id.
    """

    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated, HasWarehouseRole]

    def get_queryset(self):
        warehouse = self.get_warehouse()
        return Item.objects.filter(warehouse=warehouse).order_by("-created_at")

    def perform_create(self, serializer):
        warehouse = self.get_warehouse()
        serializer.save(warehouse=warehouse)


class ItemDetailView(WarehouseScopedMixin, generics.RetrieveUpdateAPIView):
    """
    Retrieve and update a specific item within a warehouse.
    Ensures the item belongs to the warehouse in the URL and enforces ownership.
    """

    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated, HasWarehouseRole]
    lookup_url_kwarg = "pk"

    def get_queryset(self):
        warehouse = self.get_warehouse()
        return Item.objects.filter(warehouse=warehouse)

    def update(self, request, *args, **kwargs):
        # Ensure non-negative quantity and ownership already handled by serializer and mixin
        return super().update(request, *args, **kwargs)


