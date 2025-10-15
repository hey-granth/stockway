
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    class Role(models.TextChoices):
        SHOPKEEPER = "SHOPKEEPER", "Shopkeeper"
        WAREHOUSE_ADMIN = "WAREHOUSE_ADMIN", "Warehouse Admin"
        RIDER = "RIDER", "Rider"
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"

    phone_number = models.CharField(max_length=15, unique=True)
    role = models.CharField(max_length=50, choices=Role.choices, default=Role.SHOPKEEPER)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone_number


class ShopkeeperProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shopkeeper_profile"
    )
    shop_name = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    def __str__(self):
        return self.shop_name

