from datetime import datetime
from django.db import models
from django.conf import settings


class Notification(models.Model):
    """
    Model to store order-related notifications for shopkeepers.
    """

    TYPE_CHOICES: tuple[tuple[str, str]] = (
        ("order_accepted", "Order Accepted"),
        ("order_rejected", "Order Rejected"),
        ("order_in_transit", "Order In Transit"),
        ("order_delivered", "Order Delivered"),
        ("order_cancelled", "Order Cancelled"),
        ("payment_received", "Payment Received"),
        ("payment_pending", "Payment Pending"),
        ("general", "General"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text="User receiving the notification (shopkeeper)",
    )
    notification_type: str = models.CharField(max_length=50, choices=TYPE_CHOICES)
    title: str = models.CharField(max_length=255)
    message: str = models.TextField()
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
        help_text="Related order (if applicable)",
    )
    is_read: bool = models.BooleanField(default=False)
    created_at: datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.phone_number}"


class SupportTicket(models.Model):
    """
    Model for shopkeepers to report issues or submit feedback.
    """

    CATEGORY_CHOICES: tuple[tuple[str, str]] = (
        ("order_issue", "Order Issue"),
        ("payment_issue", "Payment Issue"),
        ("delivery_issue", "Delivery Issue"),
        ("app_bug", "App Bug"),
        ("feature_request", "Feature Request"),
        ("feedback", "Feedback"),
        ("other", "Other"),
    )

    STATUS_CHOICES: tuple[tuple[str, str]] = (
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    )

    PRIORITY_CHOICES: tuple[tuple[str, str]] = (
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_tickets",
        help_text="User who created the ticket (shopkeeper)",
    )
    category: str = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    subject: str = models.CharField(max_length=255)
    description: str = models.TextField()
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_tickets",
        help_text="Related order (if applicable)",
    )
    status: str = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="open"
    )
    priority: str = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="medium"
    )
    admin_notes: str = models.TextField(
        blank=True, help_text="Internal notes for admins"
    )
    created_at: datetime = models.DateTimeField(auto_now_add=True)
    updated_at: datetime = models.DateTimeField(auto_now=True)
    resolved_at: datetime = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"Ticket #{self.id} - {self.subject} ({self.status})"
