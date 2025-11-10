from rest_framework import serializers
from .models import Payment, Payout
from orders.models import Order
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for Payment model with compact JSON response.
    """
    payment_id = serializers.IntegerField(source="id", read_only=True)
    order_id = serializers.IntegerField(source="order.id", read_only=True)
    timestamp = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "payment_id",
            "order_id",
            "status",
            "amount",
            "mode",
            "timestamp",
        ]
        read_only_fields = ["payment_id", "order_id", "timestamp"]


class PaymentInitiateSerializer(serializers.Serializer):
    """
    Serializer for initiating payment by shopkeeper.
    """
    order_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    mode = serializers.ChoiceField(choices=["upi", "cash", "credit"])

    def validate_order_id(self, value):
        """Ensure order exists."""
        try:
            order = Order.objects.get(id=value)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found.")
        return value

    def validate(self, attrs):
        """Validate payment amount matches order total and no duplicate payment."""
        order_id = attrs.get("order_id")
        amount = attrs.get("amount")

        order = Order.objects.get(id=order_id)

        # Validate amount matches order total
        if amount != order.total_amount:
            raise serializers.ValidationError(
                {"amount": f"Payment amount must equal order total: {order.total_amount}"}
            )

        # Check for existing payment
        if Payment.objects.filter(order=order, payer=self.context["request"].user).exists():
            raise serializers.ValidationError(
                {"order_id": "Payment already exists for this order."}
            )

        return attrs


class PaymentConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming or rejecting payment by warehouse admin.
    """
    payment_id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=["confirm", "reject"])

    def validate_payment_id(self, value):
        """Ensure payment exists."""
        try:
            payment = Payment.objects.get(id=value)
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment not found.")
        return value


class PayoutSerializer(serializers.ModelSerializer):
    """
    Serializer for Payout model with compact JSON response.
    """
    payout_id = serializers.IntegerField(source="id", read_only=True)
    rider_id = serializers.IntegerField(source="rider.id", read_only=True)
    warehouse_id = serializers.IntegerField(source="warehouse.id", read_only=True)
    timestamp = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Payout
        fields = [
            "payout_id",
            "rider_id",
            "warehouse_id",
            "total_distance",
            "rate_per_km",
            "computed_amount",
            "status",
            "timestamp",
        ]
        read_only_fields = ["payout_id", "rider_id", "warehouse_id", "timestamp"]


class PayoutProcessSerializer(serializers.Serializer):
    """
    Serializer for processing payouts for delivered orders.
    """
    order_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of order IDs to process payouts for. If not provided, processes all delivered orders."
    )
    rate_per_km = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("10.00"),
        help_text="Rate per kilometer for payout calculation"
    )

