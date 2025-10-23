# payments/models.py
from datetime import datetime
from decimal import Decimal
from django.db import models
from django.conf import settings
from orders.models import Order
from warehouses.models import Warehouse


class Payment(models.Model):
    """
    Model to handle payments for orders and payouts to riders.
    Tracks transactions between shopkeepers -> warehouses and warehouses -> riders.
    """

    PAYMENT_TYPE_CHOICES: tuple[tuple[str, str]] = (
        ("shopkeeper_to_warehouse", "Shopkeeper to Warehouse"),
        ("warehouse_to_rider", "Warehouse to Rider"),
    )
    STATUS_CHOICES: tuple[tuple[str, str]] = (
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )

    # Core transaction fields
    payment_type: str = models.CharField(max_length=30, choices=PAYMENT_TYPE_CHOICES)
    status: str = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    amount: Decimal = models.DecimalField(max_digits=10, decimal_places=2)

    # Related entities
    order: Order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="payments"
    )
    warehouse: Warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="transactions"
    )
    payer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments_made",
        help_text="User making the payment (shopkeeper or warehouse admin)",
    )
    payee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments_received",
        null=True,
        blank=True,
        help_text="User receiving the payment (warehouse admin or rider)",
    )
    rider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rider_payouts",
        null=True,
        blank=True,
        help_text="Rider receiving payout (only for warehouse_to_rider payments)",
    )

    # Payment metadata
    transaction_id: str = models.CharField(
        max_length=255,
        blank=True,
        unique=True,
        null=True,
        help_text="External payment gateway reference or internal transaction ID",
    )
    distance_km: Decimal = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Distance in kilometers for rider payout calculation",
    )
    payment_method: str = models.CharField(
        max_length=50,
        default="mock",
        help_text="Payment method: mock, cash, card, upi, etc.",
    )
    notes: str = models.TextField(blank=True, help_text="Additional transaction notes")

    # Timestamps
    created_at: datetime = models.DateTimeField(auto_now_add=True)
    updated_at: datetime = models.DateTimeField(auto_now=True)
    completed_at: datetime = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes: list[models.Index] = [
            models.Index(fields=["status", "payment_type"]),
            models.Index(fields=["order"]),
            models.Index(fields=["warehouse"]),
            models.Index(fields=["rider"]),
        ]

    def __str__(self):
        return f"{self.get_payment_type_display()} - {self.amount} ({self.status}) - Order #{self.order.id}"

    def save(self, *args, **kwargs):
        # Generate transaction ID if not provided
        if not self.transaction_id:
            import uuid

            self.transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)
