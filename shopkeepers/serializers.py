# shopkeepers/serializers.py
from rest_framework import serializers
from decimal import Decimal
from .models import Notification, SupportTicket


# ===== Order Management Serializers =====
class OrderItemDetailSerializer(serializers.Serializer):
    """Serializer for order items with item details."""

    id = serializers.IntegerField(read_only=True)
    item = serializers.IntegerField(read_only=True)
    item_name = serializers.CharField(read_only=True)
    quantity = serializers.IntegerField(read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)


class OrderDetailSerializer(serializers.Serializer):
    """Detailed order serializer with all related information."""

    id = serializers.IntegerField(read_only=True)
    warehouse = serializers.IntegerField(read_only=True)
    warehouse_name = serializers.CharField(read_only=True)
    warehouse_address = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    total_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    order_items = OrderItemDetailSerializer(many=True, read_only=True)
    delivery_status = serializers.CharField(read_only=True, allow_null=True)
    rider_info = serializers.DictField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class OrderUpdateSerializer(serializers.Serializer):
    """Serializer for updating order status (cancel only for shopkeeper)."""

    status = serializers.CharField()

    def validate_status(self, value):
        """Shopkeepers can only cancel orders in pending or accepted status."""
        if value != "cancelled":
            raise serializers.ValidationError("Shopkeepers can only cancel orders.")
        return value


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating orders."""

    warehouse = serializers.IntegerField()
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        help_text="List of items with 'item_id' and 'quantity'",
    )

    def validate_items(self, value):
        """Validate items list format."""
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        for item_data in value:
            if "item_id" not in item_data or "quantity" not in item_data:
                raise serializers.ValidationError(
                    "Each item must have 'item_id' and 'quantity'."
                )
            if item_data["quantity"] <= 0:
                raise serializers.ValidationError("Quantity must be positive.")
        return value

    def validate(self, attrs):
        from warehouses.models import Warehouse
        from core.services import InventoryService

        warehouse_id = attrs.get("warehouse")
        items_data = attrs.get("items")
        try:
            warehouse = Warehouse.objects.get(id=warehouse_id)
            attrs["warehouse_instance"] = warehouse
        except Warehouse.DoesNotExist:
            raise serializers.ValidationError(
                {"warehouse": "Warehouse does not exist."}
            )
        is_available, error_msg = InventoryService.check_availability(
            warehouse, items_data
        )
        if not is_available:
            raise serializers.ValidationError(error_msg)
        return attrs

    def create(self, validated_data):
        from orders.models import Order, OrderItem
        from inventory.models import Item
        from django.db import transaction

        items_data = validated_data.pop("items")
        warehouse = validated_data.pop("warehouse_instance")
        shopkeeper = self.context["request"].user
        with transaction.atomic():
            order = Order.objects.create(shopkeeper=shopkeeper, warehouse=warehouse)
            total_amount = Decimal("0.00")
            for item_data in items_data:
                item = Item.objects.select_for_update().get(id=item_data["item_id"])
                quantity = item_data["quantity"]
                price = item.price
                total_amount += price * quantity
                OrderItem.objects.create(
                    order=order, item=item, quantity=quantity, price=price
                )
                item.quantity -= quantity
                item.save()
            order.total_amount = total_amount
            order.save()
        return order


# ===== Payment Records Serializers =====
class PaymentRecordSerializer(serializers.Serializer):
    """Serializer for payment transaction history."""

    id = serializers.IntegerField(read_only=True)
    order_id = serializers.IntegerField(read_only=True)
    warehouse_name = serializers.CharField(read_only=True)
    payment_type = serializers.CharField(read_only=True)
    payment_type_display = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(read_only=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    payment_method = serializers.CharField(read_only=True)
    transaction_id = serializers.CharField(read_only=True)
    notes = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    completed_at = serializers.DateTimeField(read_only=True, allow_null=True)


class PaymentSummarySerializer(serializers.Serializer):
    """Serializer for payment summary with pending dues."""

    total_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_pending = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_failed = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_orders_count = serializers.IntegerField()
    completed_payments_count = serializers.IntegerField()


# ===== Inventory Browsing Serializers =====
class InventoryItemSerializer(serializers.Serializer):
    """Serializer for browsing warehouse inventory."""

    id = serializers.IntegerField(read_only=True)
    warehouse_id = serializers.IntegerField(read_only=True)
    warehouse_name = serializers.CharField(read_only=True)
    warehouse_address = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    sku = serializers.CharField(read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    quantity = serializers.IntegerField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


# ===== Notification Serializers =====
class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications."""

    notification_type_display = serializers.CharField(
        source="get_notification_type_display", read_only=True
    )
    order_id = serializers.IntegerField(
        source="order.id", read_only=True, allow_null=True
    )

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "notification_type_display",
            "title",
            "message",
            "order_id",
            "is_read",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "notification_type",
            "title",
            "message",
            "order_id",
            "created_at",
        ]


class NotificationMarkReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read."""

    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="List of notification IDs to mark as read. If empty, marks all as read.",
    )


# ===== Support/Feedback Serializers =====
class SupportTicketSerializer(serializers.ModelSerializer):
    """Serializer for support tickets."""

    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )

    class Meta:
        model = SupportTicket
        fields = [
            "id",
            "category",
            "category_display",
            "subject",
            "description",
            "status",
            "status_display",
            "priority",
            "priority_display",
            "created_at",
            "updated_at",
            "resolved_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "priority",
            "created_at",
            "updated_at",
            "resolved_at",
        ]


class SupportTicketCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating support tickets."""

    class Meta:
        model = SupportTicket
        fields = ["category", "subject", "description"]

    def create(self, validated_data):
        user = self.context["request"].user
        return SupportTicket.objects.create(user=user, **validated_data)


# ===== Analytics Serializers =====
class MonthlyAnalyticsSerializer(serializers.Serializer):
    """Serializer for monthly order and spending analytics."""

    month = serializers.CharField()
    year = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    completed_orders = serializers.IntegerField()
    cancelled_orders = serializers.IntegerField()
    total_spending = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)


class AnalyticsSummarySerializer(serializers.Serializer):
    """Serializer for overall analytics summary."""

    total_orders = serializers.IntegerField()
    total_spending = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_orders = serializers.IntegerField()
    completed_orders = serializers.IntegerField()
    cancelled_orders = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    monthly_data = MonthlyAnalyticsSerializer(many=True)
