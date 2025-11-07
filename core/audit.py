"""
Audit logging models for security monitoring and compliance
"""

from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import JSONField


class AuditLog(models.Model):
    """
    Audit log for tracking sensitive operations and security events
    """

    ACTION_CHOICES = [
        ("order_created", "Order Created"),
        ("order_accepted", "Order Accepted"),
        ("order_rejected", "Order Rejected"),
        ("order_assigned", "Order Assigned"),
        ("order_delivered", "Order Delivered"),
        ("order_cancelled", "Order Cancelled"),
        ("stock_deducted", "Stock Deducted"),
        ("stock_added", "Stock Added"),
        ("rider_assigned", "Rider Assigned"),
        ("payment_processed", "Payment Processed"),
        ("auth_failed", "Authentication Failed"),
        ("permission_denied", "Permission Denied"),
        ("invalid_transition", "Invalid State Transition"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, db_index=True)
    resource_type = models.CharField(
        max_length=50, db_index=True
    )  # e.g., 'order', 'item'
    resource_id = models.IntegerField(null=True, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=255, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    correlation_id = models.UUIDField(null=True, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "action", "created_at"]),
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["action", "success", "created_at"]),
        ]

    def __str__(self):
        return f"{self.action} by {self.user} at {self.created_at}"

    @classmethod
    def log_action(
        cls,
        action,
        resource_type,
        request=None,
        user=None,
        resource_id=None,
        success=True,
        error_message="",
        **metadata,
    ):
        """
        Helper method to create audit log entries

        Args:
            action: Action type from ACTION_CHOICES
            resource_type: Type of resource (order, item, etc.)
            request: HTTP request object (optional)
            user: User object (optional, extracted from request if not provided)
            resource_id: ID of affected resource (optional)
            success: Whether action succeeded
            error_message: Error message if failed
            **metadata: Additional metadata to store
        """
        if request:
            user = user or (
                request.user
                if hasattr(request, "user") and request.user.is_authenticated
                else None
            )
            ip_address = cls._get_client_ip(request)
            user_agent = request.META.get("HTTP_USER_AGENT", "")
            request_path = request.path
            request_method = request.method
            correlation_id = getattr(request, "correlation_id", None)
        else:
            ip_address = None
            user_agent = ""
            request_path = ""
            request_method = ""
            correlation_id = None

        return cls.objects.create(
            user=user,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_path=request_path,
            request_method=request_method,
            correlation_id=correlation_id,
            metadata=metadata,
            success=success,
            error_message=error_message,
        )

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
