# riders/models.py
from decimal import Decimal
from django.contrib.gis.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models as django_models
from warehouses.models import Warehouse


class Rider(models.Model):
    """
    Rider model with PostGIS location tracking for delivery management.
    """

    STATUS_CHOICES = [
        ("available", "Available"),
        ("busy", "Busy"),
        ("inactive", "Inactive"),
    ]

    AVAILABILITY_CHOICES = [
        ("available", "Available"),
        ("off-duty", "Off Duty"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rider_profile",
        help_text="User account for the rider",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="riders",
        help_text="Warehouse where rider is assigned",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="available",
        db_index=True,
        help_text="Current availability status of the rider",
    )
    availability = models.CharField(
        max_length=20,
        choices=AVAILABILITY_CHOICES,
        default="available",
        db_index=True,
        help_text="Rider availability for accepting orders",
    )
    current_location = models.PointField(
        geography=True,
        srid=4326,
        null=True,
        blank=True,
        help_text="Current GPS location of the rider",
    )
    total_earnings = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Total earnings accumulated by the rider",
    )
    device_identifier = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Unique device identifier for security",
    )
    is_suspended = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether rider is suspended by admin",
    )
    suspension_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for suspension",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "riders"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["warehouse", "status"]),
            models.Index(fields=["status"]),
            models.Index(fields=["user"]),
            models.Index(fields=["availability"]),
            models.Index(fields=["is_suspended"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(total_earnings__gte=0),
                name="rider_total_earnings_non_negative",
            ),
        ]

    def __str__(self):
        return (
            f"Rider: {self.user.full_name or self.user.email} - {self.warehouse.name}"
        )

    @property
    def latitude(self):
        """Get latitude from current location"""
        return self.current_location.y if self.current_location else None

    @property
    def longitude(self):
        """Get longitude from current location"""
        return self.current_location.x if self.current_location else None

    def set_coordinates(self, latitude, longitude):
        """Set location from lat/lng coordinates"""
        from django.contrib.gis.geos import Point

        self.current_location = Point(longitude, latitude, srid=4326)

    def save(self, *args, **kwargs):
        # Validate coordinates if location is set
        if self.current_location:
            lat, lng = self.current_location.y, self.current_location.x
            if not (-90 <= lat <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= lng <= 180):
                raise ValueError("Longitude must be between -180 and 180")
        super().save(*args, **kwargs)


class RiderNotification(django_models.Model):
    """Notifications for riders"""

    NOTIFICATION_TYPES = [
        ("order_assigned", "Order Assigned"),
        ("order_update", "Order Update"),
        ("payment", "Payment"),
        ("general", "General"),
        ("suspension", "Suspension"),
    ]

    rider = django_models.ForeignKey(
        Rider, on_delete=django_models.CASCADE, related_name="notifications"
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
        db_table = "rider_notifications"
        ordering = ["-created_at"]
        indexes = [
            django_models.Index(fields=["rider", "is_read"]),
            django_models.Index(fields=["notification_type"]),
        ]

    def __str__(self):
        return f"{self.rider.user.email} - {self.title}"


class RiderLocationHistory(django_models.Model):
    """Track rider location history for security and analytics"""

    rider = django_models.ForeignKey(
        Rider, on_delete=django_models.CASCADE, related_name="location_history"
    )
    location = models.PointField(geography=True, srid=4326)
    speed_kmh = django_models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Calculated speed in km/h",
    )
    is_suspicious = django_models.BooleanField(
        default=False,
        db_index=True,
        help_text="Flagged for abnormal movement",
    )
    distance_from_previous_km = django_models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Distance from previous location in km",
    )
    timestamp = django_models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rider_location_history"
        ordering = ["-timestamp"]
        indexes = [
            django_models.Index(fields=["rider", "timestamp"]),
            django_models.Index(fields=["is_suspicious"]),
        ]

    def __str__(self):
        return f"{self.rider.user.email} - {self.timestamp}"


