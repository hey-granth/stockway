from django.urls import path
from accounts.views import (
    SendOTPView,
    VerifyOTPView,
    LogoutView,
    RefreshTokenView,
    CurrentUserView,
)


urlpatterns = [
    # OTP Authentication endpoints
    path("send-otp/", SendOTPView.as_view(), name="send-otp"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("refresh/", RefreshTokenView.as_view(), name="refresh-token"),
    path("me/", CurrentUserView.as_view(), name="current-user"),
]
