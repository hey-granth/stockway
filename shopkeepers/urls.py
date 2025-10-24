# shopkeepers/urls.py
from django.urls import path
from .views import (
    # Order Management
    ShopkeeperOrderCreateView,
    ShopkeeperOrderListView,
    ShopkeeperOrderDetailView,
    ShopkeeperOrderUpdateView,
    ShopkeeperOrderTrackingView,
    # Payment Records
    ShopkeeperPaymentListView,
    ShopkeeperPaymentSummaryView,
    # Inventory Browsing
    ShopkeeperInventoryBrowseView,
    ShopkeeperNearbyWarehousesView,
    # Notifications
    ShopkeeperNotificationListView,
    ShopkeeperNotificationMarkReadView,
    ShopkeeperNotificationUnreadCountView,
    # Support/Feedback
    ShopkeeperSupportTicketListView,
    ShopkeeperSupportTicketCreateView,
    ShopkeeperSupportTicketDetailView,
    # Analytics
    ShopkeeperAnalyticsView,
)

app_name = 'shopkeepers'

urlpatterns = [
    # Order Management
    path('orders/create/', ShopkeeperOrderCreateView.as_view(), name='order-create'),
    path('orders/', ShopkeeperOrderListView.as_view(), name='order-list'),
    path('orders/<int:pk>/', ShopkeeperOrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:pk>/update/', ShopkeeperOrderUpdateView.as_view(), name='order-update'),
    path('orders/<int:pk>/tracking/', ShopkeeperOrderTrackingView.as_view(), name='order-tracking'),

    # Payment Records
    path('payments/', ShopkeeperPaymentListView.as_view(), name='payment-list'),
    path('payments/summary/', ShopkeeperPaymentSummaryView.as_view(), name='payment-summary'),

    # Inventory Browsing
    path('inventory/browse/', ShopkeeperInventoryBrowseView.as_view(), name='inventory-browse'),
    path('warehouses/nearby/', ShopkeeperNearbyWarehousesView.as_view(), name='warehouses-nearby'),

    # Notifications
    path('notifications/', ShopkeeperNotificationListView.as_view(), name='notification-list'),
    path('notifications/mark-read/', ShopkeeperNotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('notifications/unread-count/', ShopkeeperNotificationUnreadCountView.as_view(), name='notification-unread-count'),

    # Support/Feedback
    path('support/tickets/', ShopkeeperSupportTicketListView.as_view(), name='support-ticket-list'),
    path('support/tickets/create/', ShopkeeperSupportTicketCreateView.as_view(), name='support-ticket-create'),
    path('support/tickets/<int:pk>/', ShopkeeperSupportTicketDetailView.as_view(), name='support-ticket-detail'),

    # Analytics
    path('analytics/', ShopkeeperAnalyticsView.as_view(), name='analytics'),
]

