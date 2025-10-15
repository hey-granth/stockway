from django.db import models
from django.conf import settings
from warehouses.models import Warehouse


class RiderProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rider_profile"
    )
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, null=True, blank=True
    )
    payment_info = models.TextField()

    def __str__(self):
        return f"Rider profile for {self.user.username}"