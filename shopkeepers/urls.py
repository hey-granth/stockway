from django.urls import path
from . import views
urlpatterns = [
    # Order Management
    path("orders/create/", views.ShopkeeperOrderCreateView.as_view(), name="shopkeeper-order-create"),
    path("orders/", views.ShopkeeperOrderListView.as_view(), name="shopkeeper-order-list"),
    path("orders/<int:pk>/", views.ShopkeeperOrderDetailView.as_view(), name="shopkeeper-order-detail"),
    path("orders/<int:pk>/update/", views.ShopkeeperOrderUpdateView.as_view(), name="shopkeeper-order-update"),
    path("orders/<int:pk>/tracking/", views.ShopkeeperOrderTrackingView.as_view(), name="shopkeeper-order-tracking"),
    # Payment Records
    path("payments/", views.ShopkeeperPaymentListView.as_view(), name="shopkeeper-payment-list"),
    path("payments/summary/", views.ShopkeeperPaymentSummaryView.as_view(), name="shopkeeper-payment-summary"),
    # Inventory Browsing
    path("inventory/browse/", views.ShopkeeperInventoryBrowseView.as_view(), name="shopkeeper-inventory-browse"),
    # Warehouses
    path("warehouses/nearby/", views.ShopkeeperNearbyWarehousesView.as_view(), name="shopkeeper-warehouses-nearby"),
    # Notifications
    path("notifications/", views.ShopkeeperNotificationListView.as_view(), name="shopkeeper-notifications"),
    path("notifications/mark-read/", views.ShopkeeperNotificationMarkReadView.as_view(), name="shopkeeper-notifications-mark-read"),
    path("notifications/unread-count/", views.ShopkeeperNotificationUnreadCountView.as_view(), name="shopkeeper-notifications-unread-count"),
    # Support Tickets
    path("support/tickets/", views.ShopkeeperSupportTicketListView.as_view(), name="shopkeeper-support-tickets"),
    path("support/tickets/create/", views.ShopkeeperSupportTicketCreateView.as_view(), name="shopkeeper-support-ticket-create"),
    path("support/tickets/<int:pk>/", views.ShopkeeperSupportTicketDetailView.as_view(), name="shopkeeper-support-ticket-detail"),
    # Analytics
    path("analytics/", views.ShopkeeperAnalyticsView.as_view(), name="shopkeeper-analytics"),
]
