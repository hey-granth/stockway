# delivery/models.py
from datetime import datetime
from decimal import Decimal
from django.db import models
from django.conf import settings
from orders.models import Order


class Delivery(models.Model):
    """
    Model to track order deliveries.
    """

    STATUS_CHOICES: tuple[tuple[str, str]] = (
        ("assigned", "Assigned"),
        ("in_transit", "In Transit"),
        ("delivered", "Delivered"),
        ("failed", "Failed"),
    )

    order: Order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="delivery"
    )
    rider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deliveries",
    )
    status: str = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="assigned"
    )
    delivery_fee: Decimal = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    created_at: datetime = models.DateTimeField(auto_now_add=True)
    updated_at: datetime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Delivery for Order #{self.order.id}"
