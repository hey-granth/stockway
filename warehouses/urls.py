from django.urls import path
from .views import (
    WarehouseOnboardingView,
    WarehouseCreateView,
    WarehouseDetailView,
    WarehouseOrderListView,
    WarehouseOrderConfirmView,
    WarehouseOrderAssignView,
)
from inventory.views import ItemListCreateView, ItemDetailView

urlpatterns = [
    path("onboarding/", WarehouseOnboardingView.as_view(), name="warehouse-onboarding"),
    path("", WarehouseCreateView.as_view(), name="warehouse-create"),
    path("<int:pk>/", WarehouseDetailView.as_view(), name="warehouse-detail"),
    # Inventory endpoints scoped to a warehouse
    path("<int:warehouse_id>/items/", ItemListCreateView.as_view(), name="warehouse-items"),
    path(
        "<int:warehouse_id>/items/<int:pk>/",
        ItemDetailView.as_view(),
        name="warehouse-item-detail",
    ),
    # Order management endpoints for warehouse admins
    path(
        "<int:warehouse_id>/orders/",
        WarehouseOrderListView.as_view(),
        name="warehouse-orders",
    ),
    path(
        "<int:warehouse_id>/orders/<int:order_id>/confirm/",
        WarehouseOrderConfirmView.as_view(),
        name="warehouse-order-confirm",
    ),
    path(
        "<int:warehouse_id>/orders/<int:order_id>/assign/",
        WarehouseOrderAssignView.as_view(),
        name="warehouse-order-assign",
    ),
]
