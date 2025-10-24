# shopkeepers/serializers.py
from rest_framework import serializers
from decimal import Decimal
from .models import Notification, SupportTicket
from orders.models import Order, OrderItem
from payments.models import Payment
from inventory.models import Item
from delivery.models import Delivery
from warehouses.models import Warehouse


# ===== Order Management Serializers =====

class OrderItemDetailSerializer(serializers.ModelSerializer):
    """Serializer for order items with item details."""

    item_name = serializers.CharField(source="item.name", read_only=True)
    item_sku = serializers.CharField(source="item.sku", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "item", "item_name", "item_sku", "quantity", "price"]
        read_only_fields = ["id", "item_name", "item_sku", "price"]


class OrderDetailSerializer(serializers.ModelSerializer):
    """Detailed order serializer with all related information."""

    order_items = OrderItemDetailSerializer(many=True, read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    warehouse_address = serializers.CharField(source="warehouse.address", read_only=True)

    # Delivery and rider info
    delivery_status = serializers.SerializerMethodField()
    rider_info = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "warehouse",
            "warehouse_name",
            "warehouse_address",
            "status",
            "total_amount",
            "order_items",
            "delivery_status",
            "rider_info",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "warehouse_name",
            "warehouse_address",
            "total_amount",
            "created_at",
            "updated_at",
        ]

    def get_delivery_status(self, obj) -> str | None:
        try:
            return obj.delivery.status
        except Delivery.DoesNotExist:
            return None

    def get_rider_info(self, obj) -> dict | None:
        try:
            delivery = obj.delivery
            if delivery.rider:
                return {
                    "rider_id": delivery.rider.id,
                    "rider_phone": delivery.rider.phone_number,
                    "delivery_fee": str(delivery.delivery_fee),
                }
            return None
        except Delivery.DoesNotExist:
            return None


class OrderUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating order status (cancel only for shopkeeper)."""

    class Meta:
        model = Order
        fields = ["status"]

    def validate_status(self, value):
        """Shopkeepers can only cancel orders in pending or accepted status."""
        instance = self.instance
        if value != "cancelled":
            raise serializers.ValidationError(
                "Shopkeepers can only cancel orders."
            )
        if instance.status not in ["pending", "accepted"]:
            raise serializers.ValidationError(
                f"Cannot cancel order with status: {instance.status}"
            )
        return value


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating orders."""

    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        help_text="List of items with 'item_id' and 'quantity'"
    )

    class Meta:
        model = Order
        fields = ["warehouse", "items"]

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
        warehouse = attrs.get("warehouse")
        items_data = attrs.get("items")

        # Check if warehouse exists
        if not Warehouse.objects.filter(id=warehouse.id).exists():
            raise serializers.ValidationError({"warehouse": "Warehouse does not exist."})

        # Check inventory for each item
        for item_data in items_data:
            item_id = item_data.get("item_id")
            quantity = item_data.get("quantity")

            try:
                inventory_item = Item.objects.get(id=item_id, warehouse=warehouse)
                if inventory_item.quantity < quantity:
                    raise serializers.ValidationError(
                        f"Not enough stock for {inventory_item.name}. "
                        f"Available: {inventory_item.quantity}, Requested: {quantity}"
                    )
            except Item.DoesNotExist:
                raise serializers.ValidationError(
                    f"Item with ID {item_id} not found in this warehouse."
                )

        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        shopkeeper = self.context["request"].user

        order = Order.objects.create(
            shopkeeper=shopkeeper,
            warehouse=validated_data["warehouse"]
        )

        total_amount = Decimal("0.00")
        for item_data in items_data:
            item = Item.objects.get(id=item_data["item_id"])
            quantity = item_data["quantity"]
            price = item.price
            total_amount += price * quantity

            OrderItem.objects.create(
                order=order,
                item=item,
                quantity=quantity,
                price=price
            )

            # Update inventory
            item.quantity -= quantity
            item.save()

        order.total_amount = total_amount
        order.save()

        return order


# ===== Payment Records Serializers =====

class PaymentRecordSerializer(serializers.ModelSerializer):
    """Serializer for payment transaction history."""

    order_id = serializers.IntegerField(source="order.id", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    payment_type_display = serializers.CharField(
        source="get_payment_type_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "order_id",
            "warehouse_name",
            "payment_type",
            "payment_type_display",
            "status",
            "status_display",
            "amount",
            "payment_method",
            "transaction_id",
            "notes",
            "created_at",
            "completed_at",
        ]
        read_only_fields = fields


class PaymentSummarySerializer(serializers.Serializer):
    """Serializer for payment summary with pending dues."""

    total_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_pending = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_failed = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_orders_count = serializers.IntegerField()
    completed_payments_count = serializers.IntegerField()


# ===== Inventory Browsing Serializers =====

class InventoryItemSerializer(serializers.ModelSerializer):
    """Serializer for browsing warehouse inventory."""

    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    warehouse_id = serializers.IntegerField(source="warehouse.id", read_only=True)
    warehouse_address = serializers.CharField(source="warehouse.address", read_only=True)
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            "id",
            "warehouse_id",
            "warehouse_name",
            "warehouse_address",
            "name",
            "description",
            "sku",
            "price",
            "quantity",
            "in_stock",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_in_stock(self, obj) -> bool:
        return obj.quantity > 0


# ===== Notification Serializers =====

class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications."""

    notification_type_display = serializers.CharField(
        source="get_notification_type_display", read_only=True
    )
    order_id = serializers.IntegerField(source="order.id", read_only=True, allow_null=True)

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
        read_only_fields = ["id", "notification_type", "title", "message", "order_id", "created_at"]


class NotificationMarkReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read."""

    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="List of notification IDs to mark as read. If empty, marks all as read."
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
    order_id = serializers.IntegerField(source="order.id", read_only=True, allow_null=True)

    class Meta:
        model = SupportTicket
        fields = [
            "id",
            "category",
            "category_display",
            "subject",
            "description",
            "order_id",
            "status",
            "status_display",
            "priority",
            "priority_display",
            "created_at",
            "updated_at",
            "resolved_at",
        ]
        read_only_fields = ["id", "status", "priority", "created_at", "updated_at", "resolved_at"]


class SupportTicketCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating support tickets."""

    class Meta:
        model = SupportTicket
        fields = ["category", "subject", "description", "order"]

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

