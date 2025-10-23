# inventory/models.py
from datetime import datetime
from decimal import Decimal
from django.db import models
from warehouses.models import Warehouse


class Item(models.Model):
    """
    Model to store inventory items in a warehouse.
    """

    warehouse: Warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="items"
    )
    name: str = models.CharField(max_length=255)
    description: str = models.TextField(blank=True)
    sku: str = models.CharField(max_length=100, unique=True)
    price: Decimal = models.DecimalField(max_digits=10, decimal_places=2)
    quantity: int = models.PositiveIntegerField(default=0)
    created_at: datetime = models.DateTimeField(auto_now_add=True)
    updated_at: datetime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"
