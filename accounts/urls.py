from django.urls import path
from .views import RequestOTP, VerifyOTP

urlpatterns = [
    path("request-otp/", RequestOTP.as_view(), name="request-otp"),
    path("verify-otp/", VerifyOTP.as_view(), name="verify-otp"),
]
