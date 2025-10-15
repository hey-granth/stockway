from django.urls import path
from .views import RiderProfileView

urlpatterns = [
    path("profile/", RiderProfileView.as_view(), name="rider-profile"),
]
