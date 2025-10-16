from django.urls import path
from .views import WarehouseOnboardingView, WarehouseCreateView, WarehouseDetailView
from inventory.views import ItemListCreateView, ItemDetailView

urlpatterns = [
    path("onboarding/", WarehouseOnboardingView.as_view(), name="warehouse-onboarding"),
    path("", WarehouseCreateView.as_view(), name="warehouse-create"),
    path("<int:pk>/", WarehouseDetailView.as_view(), name="warehouse-detail"),

    # Inventory endpoints scoped to a warehouse
    path("<int:warehouse_id>/items/", ItemListCreateView.as_view(), name="warehouse-items"),
    path("<int:warehouse_id>/items/<int:pk>/", ItemDetailView.as_view(), name="warehouse-item-detail"),
]
