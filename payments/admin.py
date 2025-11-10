from django.contrib import admin
from .models import Payment, Payout


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """
    Admin interface for Payment model.
    """
    list_display = [
        "id",
        "order",
        "payer",
        "payee",
        "amount",
        "mode",
        "status",
        "created_at",
    ]

    list_filter = [
        "status",
        "mode",
        "created_at",
    ]

    search_fields = [
        "payer__email",
        "payer__phone_number",
        "payee__email",
        "payee__phone_number",
        "order__id",
    ]

    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Transaction Information",
            {
                "fields": (
                    "order",
                    "payer",
                    "payee",
                    "amount",
                    "mode",
                    "status",
                )
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
        qs = super().get_queryset(request)
        return qs.select_related("order", "payer", "payee")


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    """
    Admin interface for Payout model.
    """
    list_display = [
        "id",
        "rider",
        "warehouse",
        "total_distance",
        "rate_per_km",
        "computed_amount",
        "status",
        "created_at",
    ]

    list_filter = [
        "status",
        "created_at",
        "warehouse",
    ]

    search_fields = [
        "rider__user__email",
        "rider__user__phone_number",
        "warehouse__name",
    ]

    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Payout Information",
            {
                "fields": (
                    "rider",
                    "warehouse",
                    "total_distance",
                    "rate_per_km",
                    "computed_amount",
                    "status",
                )
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
        qs = super().get_queryset(request)
        return qs.select_related("rider", "warehouse")
