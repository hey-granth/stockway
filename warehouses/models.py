from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.core.validators import MinValueValidator
from django.db import models as django_models
from django.utils import timezone
from decimal import Decimal


class WarehouseManager(django_models.Manager):
    """Default manager — excludes soft-deleted warehouses."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllObjectsManager(django_models.Manager):
    """Manager that returns ALL warehouses including soft-deleted ones."""

    def get_queryset(self):
        return super().get_queryset()


class Warehouse(models.Model):
    """Warehouse profile with PostGIS location support"""

    admin = django_models.ForeignKey(
        "accounts.User", on_delete=django_models.CASCADE, related_name="warehouses"
    )
    name = django_models.CharField(max_length=255)
    address = django_models.TextField()
    contact_number = django_models.CharField(max_length=20)
    location = models.PointField(
        geography=True, srid=4326, null=True, blank=True, spatial_index=True
    )  # PostGIS Point field
    is_active = django_models.BooleanField(default=True)
    is_approved = django_models.BooleanField(default=False)
    deleted_at = django_models.DateTimeField(null=True, blank=True)
    created_at = django_models.DateTimeField(auto_now_add=True)
    updated_at = django_models.DateTimeField(auto_now=True)

    # Managers
    objects = WarehouseManager()
    all_objects = AllObjectsManager()

    class Meta:
        db_table = "warehouses"
        ordering = ["-created_at"]
        indexes = [
            django_models.Index(fields=["is_active", "is_approved"]),
            django_models.Index(fields=["admin"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.admin.email}"

    def soft_delete(self):
        """Mark the warehouse as deleted without removing the row."""
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save(update_fields=["deleted_at", "is_active", "updated_at"])

    @property
    def latitude(self):
        return self.location.y if self.location else None

    @property
    def longitude(self):
        return self.location.x if self.location else None

    def set_coordinates(self, latitude, longitude):
        """Set location from lat/lng coordinates"""
        self.location = Point(longitude, latitude, srid=4326)

    def save(self, *args, **kwargs):
        # Validate coordinates if location is set
        if self.location:
            lat, lng = self.location.y, self.location.x
            if not (-90 <= lat <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= lng <= 180):
                raise ValueError("Longitude must be between -180 and 180")
        super().save(*args, **kwargs)


class WarehouseNotification(django_models.Model):
    """Notifications for warehouse admins"""

    NOTIFICATION_TYPES = [
        ("order", "Order"),
        ("stock", "Stock"),
        ("general", "General"),
        ("payment", "Payment"),
        ("rider", "Rider"),
    ]

    warehouse = django_models.ForeignKey(
        Warehouse, on_delete=django_models.CASCADE, related_name="notifications"
    )
    notification_type = django_models.CharField(
        max_length=20, choices=NOTIFICATION_TYPES
    )
    title = django_models.CharField(max_length=255)
    message = django_models.TextField()
    is_read = django_models.BooleanField(default=False)
    metadata = django_models.JSONField(default=dict, blank=True)
    created_at = django_models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "warehouse_notifications"
        ordering = ["-created_at"]
        indexes = [
            django_models.Index(fields=["warehouse", "is_read"]),
            django_models.Index(fields=["notification_type"]),
        ]

    def __str__(self):
        return f"{self.warehouse.name} - {self.title}"


class RiderPayout(django_models.Model):
    """Rider payment tracking for warehouses"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    warehouse = django_models.ForeignKey(
        Warehouse, on_delete=django_models.CASCADE, related_name="rider_payouts"
    )
    rider = django_models.ForeignKey(
        "riders.Rider", on_delete=django_models.CASCADE, related_name="payouts"
    )
    order = django_models.ForeignKey(
        "orders.Order", on_delete=django_models.CASCADE, related_name="rider_payouts"
    )
    base_rate = django_models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    distance_km = django_models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    distance_rate = django_models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    total_amount = django_models.DecimalField(
        max_digits=10, decimal_places=2, editable=False
    )
    status = django_models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    payment_reference = django_models.CharField(max_length=255, blank=True)
    created_at = django_models.DateTimeField(auto_now_add=True)
    paid_at = django_models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "rider_payouts"
        ordering = ["-created_at"]
        indexes = [
            django_models.Index(fields=["warehouse", "status"]),
            django_models.Index(fields=["rider", "status"]),
        ]

    def __str__(self):
        return f"Payout for {self.rider} - Order #{self.order_id}"

    def calculate_total(self):
        """Calculate total payout amount"""
        return self.base_rate + (self.distance_km * self.distance_rate)

    def save(self, *args, **kwargs):
        # Auto-calculate total amount
        self.total_amount = self.calculate_total()
        super().save(*args, **kwargs)
