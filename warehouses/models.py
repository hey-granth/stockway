# warehouses/models.py
from datetime import datetime
from decimal import Decimal
from django.contrib.gis.db.models import PointField
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.conf import settings


class Warehouse(models.Model):
    """
    Model to store warehouse information with PostGIS geospatial support.
    """

    name: str = models.CharField(max_length=255)
    address: str = models.TextField()

    # PostGIS PointField for geospatial queries
    location: PointField = gis_models.PointField(
        geography=True,
        srid=4326,
        help_text="Geographic location (longitude, latitude)",
        null=True,
        blank=True,
    )

    # Keep legacy fields for backward compatibility during migration
    latitude: Decimal = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude: Decimal = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="warehouses"
    )
    created_at: datetime = models.DateTimeField(auto_now_add=True)
    updated_at: datetime = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["location"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs) -> None:
        """
        Auto-sync location PointField with latitude/longitude fields.
        """
        from django.contrib.gis.geos import Point

        # If latitude and longitude are provided, update location
        if self.latitude is not None and self.longitude is not None:
            self.location = Point(
                float(self.longitude), float(self.latitude), srid=4326
            )
        # If location is provided, update latitude and longitude
        elif self.location:
            self.longitude = self.location.x
            self.latitude = self.location.y

        super().save(*args, **kwargs)
