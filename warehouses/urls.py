from django.urls import path
from .views import WarehouseOnboardingView

urlpatterns = [
    path("onboarding/", WarehouseOnboardingView.as_view(), name="warehouse-onboarding"),
]
