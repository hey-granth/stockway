# orders/models.py
from datetime import datetime
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from accounts.models import User
from warehouses.models import Warehouse
from inventory.models import Item


class Order(models.Model):
    """
    Model to store customer orders with enhanced security constraints.
    """

    STATUS_CHOICES: tuple[tuple[str, str]] = (
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("assigned", "Assigned"),
        ("in_transit", "In Transit"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    )

    shopkeeper: User = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    warehouse: Warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="orders"
    )
    status: str = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True
    )
    total_amount: Decimal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    rejection_reason: str = models.TextField(blank=True, null=True)
    created_at: datetime = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at: datetime = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"
        indexes = [
            models.Index(fields=["shopkeeper", "status"]),
            models.Index(fields=["warehouse", "status"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["warehouse", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(total_amount__gte=0),
                name="order_total_amount_non_negative",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id} by {self.shopkeeper.phone_number or self.shopkeeper.email}"


class OrderItem(models.Model):
    """
    Model for items within an order with validation constraints.
    """

    order: Order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_items"
    )
    item: Item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity: int = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price: Decimal = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )

    class Meta:
        db_table = "order_items"
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["item"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gte=1), name="order_item_quantity_positive"
            ),
            models.CheckConstraint(
                check=models.Q(price__gte=0), name="order_item_price_non_negative"
            ),
        ]

    def __str__(self):
        return f"{self.quantity} of {self.item.name} in Order #{self.order.id}"
