from django.urls import path
from .views import RiderProfileView, RiderOrderListView, RiderOrderDeliverView

urlpatterns = [
    path("profile/", RiderProfileView.as_view(), name="rider-profile"),
    path("orders/", RiderOrderListView.as_view(), name="rider-orders"),
    path(
        "orders/<int:order_id>/deliver/",
        RiderOrderDeliverView.as_view(),
        name="rider-order-deliver",
    ),
]
