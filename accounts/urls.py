from django.urls import path
from .views import RequestOTP, VerifyOTP, ShopkeeperProfileView, CustomerProfileUpdateView

urlpatterns = [
    path("request-otp/", RequestOTP.as_view(), name="request-otp"),
    path("verify-otp/", VerifyOTP.as_view(), name="verify-otp"),
    path(
        "shopkeeper/profile/",
        ShopkeeperProfileView.as_view(),
        name="shopkeeper-profile",
    ),
    path(
        "customers/profile/",
        CustomerProfileUpdateView.as_view(),
        name="customer-profile",
    ),
]
