# riders/urls.py
from django.urls import path
from .views import (
    RiderRegistrationView,
    RiderProfileView,
    RiderOrdersView,
    RiderOrderUpdateView,
    RiderLocationUpdateView,
    WarehouseRidersListView,
    RiderDetailView,
    # New advanced features
    RiderEarningsView,
    RiderHistoryView,
    RiderLiveLocationView,
    RiderPerformanceView,
    RiderAvailabilityUpdateView,
    RiderNotificationsView,
    RiderNotificationMarkReadView,
    WarehouseActiveRidersView,
    WarehouseRiderMetricsView,
    AdminRiderManagementView,
    AdminRiderPayoutExportView,
)

app_name = "riders"

urlpatterns = [
    # Rider endpoints
    path("rider/register/", RiderRegistrationView.as_view(), name="rider-register"),
    path("rider/profile/", RiderProfileView.as_view(), name="rider-profile"),
    path("rider/orders/", RiderOrdersView.as_view(), name="rider-orders"),
    path(
        "rider/orders/update/",
        RiderOrderUpdateView.as_view(),
        name="rider-order-update",
    ),
    path(
        "rider/location/update/",
        RiderLocationUpdateView.as_view(),
        name="rider-location-update",
    ),

    # New rider advanced features
    path("rider/earnings/", RiderEarningsView.as_view(), name="rider-earnings"),
    path("rider/history/", RiderHistoryView.as_view(), name="rider-history"),
    path("rider/live-location/", RiderLiveLocationView.as_view(), name="rider-live-location"),
    path("rider/performance/", RiderPerformanceView.as_view(), name="rider-performance"),
    path("rider/availability/update/", RiderAvailabilityUpdateView.as_view(), name="rider-availability-update"),
    path("rider/notifications/", RiderNotificationsView.as_view(), name="rider-notifications"),
    path("rider/notifications/<int:pk>/mark-read/", RiderNotificationMarkReadView.as_view(), name="rider-notification-mark-read"),

    # Warehouse admin endpoints
    path(
        "warehouse/riders/",
        WarehouseRidersListView.as_view(),
        name="warehouse-riders-list",
    ),
    path("warehouse/riders/<int:pk>/", RiderDetailView.as_view(), name="rider-detail"),
    path("warehouse/riders/active/", WarehouseActiveRidersView.as_view(), name="warehouse-active-riders"),
    path("warehouse/riders/metrics/", WarehouseRiderMetricsView.as_view(), name="warehouse-rider-metrics"),

    # Admin control endpoints
    path("admin/riders/manage/", AdminRiderManagementView.as_view(), name="admin-rider-management"),
    path("admin/riders/export/payouts/", AdminRiderPayoutExportView.as_view(), name="admin-rider-payout-export"),
]
