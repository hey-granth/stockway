# riders/admin.py
from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from .models import Rider, RiderNotification, RiderLocationHistory


@admin.register(Rider)
class RiderAdmin(GISModelAdmin):
    """
    Admin interface for Rider model with PostGIS support.
    """

    list_display = [
        "id",
        "user",
        "warehouse",
        "status",
        "availability",
        "is_suspended",
        "total_earnings",
        "created_at",
    ]
    list_filter = ["status", "availability", "is_suspended", "warehouse", "created_at"]
    search_fields = [
        "user__email",
        "user__full_name",
        "user__phone_number",
        "warehouse__name",
    ]
    readonly_fields = ["created_at", "updated_at", "total_earnings"]
    ordering = ["-created_at"]

    fieldsets = (
        (
            "Rider Information",
            {
                "fields": (
                    "user",
                    "warehouse",
                    "status",
                    "availability",
                )
            },
        ),
        (
            "Location",
            {
                "fields": ("current_location",),
                "description": "GPS location tracking for the rider",
            },
        ),
        (
            "Security",
            {
                "fields": (
                    "device_identifier",
                    "is_suspended",
                    "suspension_reason",
                ),
                "description": "Security and suspension management",
            },
        ),
        (
            "Earnings",
            {
                "fields": ("total_earnings",),
                "description": "Total earnings accumulated",
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related("user", "warehouse")


@admin.register(RiderNotification)
class RiderNotificationAdmin(admin.ModelAdmin):
    """Admin interface for Rider Notifications"""

    list_display = [
        "id",
        "rider",
        "notification_type",
        "title",
        "is_read",
        "created_at",
    ]
    list_filter = ["notification_type", "is_read", "created_at"]
    search_fields = ["rider__user__email", "title", "message"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]

    fieldsets = (
        (
            "Notification Details",
            {
                "fields": (
                    "rider",
                    "notification_type",
                    "title",
                    "message",
                    "is_read",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": ("metadata",),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("rider", "rider__user")


@admin.register(RiderLocationHistory)
class RiderLocationHistoryAdmin(GISModelAdmin):
    """Admin interface for Rider Location History"""

    list_display = [
        "id",
        "rider",
        "speed_kmh",
        "distance_from_previous_km",
        "is_suspicious",
        "timestamp",
    ]
    list_filter = ["is_suspicious", "timestamp"]
    search_fields = ["rider__user__email"]
    readonly_fields = ["timestamp"]
    ordering = ["-timestamp"]

    fieldsets = (
        (
            "Location Details",
            {
                "fields": (
                    "rider",
                    "location",
                )
            },
        ),
        (
            "Tracking Metrics",
            {
                "fields": (
                    "speed_kmh",
                    "distance_from_previous_km",
                    "is_suspicious",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("timestamp",),
            },
        ),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("rider", "rider__user")

