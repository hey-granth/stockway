# payments/models.py
from datetime import datetime
from decimal import Decimal
from django.db import models
from django.conf import settings
from orders.models import Order
from warehouses.models import Warehouse
from riders.models import Rider


class Payment(models.Model):
    """
    Model to handle payments from shopkeepers to warehouses for orders.
    """

    MODE_CHOICES: tuple[tuple[str, str], ...] = (
        ("upi", "UPI"),
        ("cash", "Cash"),
        ("credit", "Credit"),
    )
    STATUS_CHOICES: tuple[tuple[str, str], ...] = (
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )

    # Related entities
    order: Order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="payments"
    )
    payer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments_made",
        help_text="Shopkeeper making the payment",
    )
    payee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments_received",
        null=True,
        blank=True,
        help_text="Warehouse receiving the payment",
    )

    # Transaction fields
    amount: Decimal = models.DecimalField(max_digits=10, decimal_places=2)
    mode: str = models.CharField(max_length=20, choices=MODE_CHOICES, default="cash")
    status: str = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )

    # Timestamps
    created_at: datetime = models.DateTimeField(auto_now_add=True)
    updated_at: datetime = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [["order", "payer"]]
        indexes: list[models.Index] = [
            models.Index(fields=["status"]),
            models.Index(fields=["order"]),
            models.Index(fields=["payer"]),
            models.Index(fields=["payee"]),
        ]

    def __str__(self):
        return f"Payment #{self.id} - Order #{self.order.id} - {self.amount} ({self.status})"


class Payout(models.Model):
    """
    Model to track payouts to riders for delivered orders.
    """

    STATUS_CHOICES: tuple[tuple[str, str], ...] = (
        ("pending", "Pending"),
        ("settled", "Settled"),
    )

    # Related entities
    rider = models.ForeignKey(
        Rider,
        on_delete=models.CASCADE,
        related_name="payment_payouts",
        help_text="Rider receiving the payout",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="payouts",
        help_text="Warehouse processing the payout",
    )

    # Payout calculation fields
    total_distance: float = models.FloatField(help_text="Total distance in kilometers")
    rate_per_km: Decimal = models.DecimalField(
        max_digits=6, decimal_places=2, help_text="Rate per kilometer"
    )
    computed_amount: Decimal = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Computed payout amount"
    )
    status: str = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )

    # Timestamps
    created_at: datetime = models.DateTimeField(auto_now_add=True)
    updated_at: datetime = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes: list[models.Index] = [
            models.Index(fields=["status"]),
            models.Index(fields=["rider"]),
            models.Index(fields=["warehouse"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Payout #{self.id} - Rider {self.rider.id} - {self.computed_amount} ({self.status})"
