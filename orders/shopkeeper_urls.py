# Shopkeeper-specific order URLs
from django.urls import path
from orders.views import (
    OrderCreateView,
    ShopkeeperOrderListView,
    ShopkeeperOrderDetailView,
)

app_name = "shopkeeper"

urlpatterns = [
    path("orders/create/", OrderCreateView.as_view(), name="order-create"),
    path("orders/", ShopkeeperOrderListView.as_view(), name="order-list"),
    path("orders/<int:pk>/", ShopkeeperOrderDetailView.as_view(), name="order-detail"),
]
