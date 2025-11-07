# orders/urls.py
from django.urls import path
from .views import (
    OrderCreateView,
    ShopkeeperOrderListView,
    ShopkeeperOrderDetailView,
    WarehouseOrderListView,
    WarehouseOrderDetailView,
    WarehousePendingOrdersView,
    OrderAcceptView,
    OrderRejectView,
    OrderAssignmentView,
)

app_name = "orders"

urlpatterns = [
    # Shopkeeper endpoints
    path("shopkeeper/orders/create/", OrderCreateView.as_view(), name="order-create"),
    path(
        "shopkeeper/orders/",
        ShopkeeperOrderListView.as_view(),
        name="shopkeeper-order-list",
    ),
    path(
        "shopkeeper/orders/<int:pk>/",
        ShopkeeperOrderDetailView.as_view(),
        name="shopkeeper-order-detail",
    ),
    # Warehouse endpoints
    path(
        "warehouse/orders/",
        WarehouseOrderListView.as_view(),
        name="warehouse-order-list",
    ),
    path(
        "warehouse/orders/pending/",
        WarehousePendingOrdersView.as_view(),
        name="warehouse-pending-orders",
    ),
    path(
        "warehouse/orders/<int:pk>/",
        WarehouseOrderDetailView.as_view(),
        name="warehouse-order-detail",
    ),
    path(
        "warehouse/orders/<int:pk>/accept/",
        OrderAcceptView.as_view(),
        name="order-accept",
    ),
    path(
        "warehouse/orders/<int:pk>/reject/",
        OrderRejectView.as_view(),
        name="order-reject",
    ),
    path(
        "warehouse/orders/assign/", OrderAssignmentView.as_view(), name="order-assign"
    ),
]
