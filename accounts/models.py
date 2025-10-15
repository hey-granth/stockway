from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        SHOPKEEPER = "SHOPKEEPER", "Shopkeeper"
        WAREHOUSE_ADMIN = "WAREHOUSE_ADMIN", "Warehouse Admin"
        RIDER = "RIDER", "Rider"
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"

    phone_number = models.CharField(max_length=15, unique=True)
    role = models.CharField(max_length=50, choices=Role.choices)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone_number
