from django.contrib import admin
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/accounts/", include("accounts.urls")),
    path(
        "api/shopkeeper/", include("orders.shopkeeper_urls")
    ),  # Shopkeeper order endpoints
    path(
        "api/warehouse/", include("orders.warehouse_urls")
    ),  # Warehouse order endpoints
    path("api/warehouses/", include("warehouses.urls")),
    path("api/inventory/", include("inventory.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/shopkeepers/", include("shopkeepers.urls")),
    path("api/riders/", include("riders.urls")),
    path("api/payments/", include("payments.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/analytics/", include("analytics.urls")),
]
