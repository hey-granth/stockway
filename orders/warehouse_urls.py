# Warehouse-specific order URLs
from django.urls import path
from orders.views import (
    WarehouseOrderListView,
    WarehouseOrderDetailView,
    WarehousePendingOrdersView,
    OrderAcceptView,
    OrderRejectView,
    OrderAssignmentView,
)

app_name = "warehouse"

urlpatterns = [
    path("orders/", WarehouseOrderListView.as_view(), name="order-list"),
    path(
        "orders/pending/", WarehousePendingOrdersView.as_view(), name="pending-orders"
    ),
    path("orders/<int:pk>/", WarehouseOrderDetailView.as_view(), name="order-detail"),
    path("orders/<int:pk>/accept/", OrderAcceptView.as_view(), name="order-accept"),
    path("orders/<int:pk>/reject/", OrderRejectView.as_view(), name="order-reject"),
    path("orders/assign/", OrderAssignmentView.as_view(), name="order-assign"),
]
