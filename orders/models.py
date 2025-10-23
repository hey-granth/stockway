# orders/models.py
from datetime import datetime
from decimal import Decimal
from django.db import models
from django.conf import settings
from accounts.models import User
from warehouses.models import Warehouse
from inventory.models import Item


class Order(models.Model):
    """
    Model to store customer orders.
    """

    STATUS_CHOICES: tuple[tuple[str, str]] = (
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("in_transit", "In Transit"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    )

    shopkeeper: User = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    warehouse: User = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="orders"
    )
    status: str = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    total_amount: Decimal = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    created_at: datetime = models.DateTimeField(auto_now_add=True)
    updated_at: datetime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} by {self.shopkeeper.username}"


class OrderItem(models.Model):
    """
    Model for items within an order.
    """

    order: Order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_items"
    )
    item: Item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity: int = models.PositiveIntegerField()
    price: Decimal = models.DecimalField(
        max_digits=10, decimal_places=2
    )  # Price at the time of order

    def __str__(self):
        return f"{self.quantity} of {self.item.name} in Order #{self.order.id}"
