# riders/urls.py
from django.urls import path
from .views import (
    RiderProfileView,
    RiderOrderListView,
    RiderOrderUpdateView,
)

app_name = "riders"

urlpatterns = [
    # Rider profile
    path("profile/", RiderProfileView.as_view(), name="rider-profile"),
    # Rider order operations
    path("orders/", RiderOrderListView.as_view(), name="rider-order-list"),
    path("orders/<int:pk>/", RiderOrderUpdateView.as_view(), name="rider-order-update"),
]
