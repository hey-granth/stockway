from typing import Literal
from rest_framework import serializers
from .models import Payment
from django.contrib.auth import get_user_model
from django.utils import timezone


User = get_user_model()


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for Payment model with detailed information.
    """

    payment_type_display = serializers.CharField(
        source="get_payment_type_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    payer_phone = serializers.CharField(source="payer.phone_number", read_only=True)
    payee_phone = serializers.CharField(source="payee.phone_number", read_only=True)
    rider_phone = serializers.CharField(
        source="rider.phone_number", read_only=True, allow_null=True
    )
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    order_id = serializers.IntegerField(source="order.id", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "payment_type",
            "payment_type_display",
            "status",
            "status_display",
            "amount",
            "order",
            "order_id",
            "warehouse",
            "warehouse_name",
            "payer",
            "payer_phone",
            "payee",
            "payee_phone",
            "rider",
            "rider_phone",
            "transaction_id",
            "distance_km",
            "payment_method",
            "notes",
            "created_at",
            "updated_at",
            "completed_at",
        ]
        read_only_fields = [
            "transaction_id",
            "created_at",
            "updated_at",
            "completed_at",
        ]


class CreateShopkeeperPaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for shopkeepers to create payments to warehouses for orders.
    """

    class Meta:
        model = Payment
        fields = ["order", "amount", "payment_method", "notes"]

    def validate_order(self, value):
        """Ensure the order exists and belongs to the requesting shopkeeper."""
        request = self.context.get("request")
        if not value.shopkeeper == request.user:
            raise serializers.ValidationError(
                "You can only make payments for your own orders."
            )
        if value.status not in ["accepted", "in_transit", "delivered"]:
            raise serializers.ValidationError(
                "Cannot make payment for orders that are not accepted."
            )
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        order = validated_data["order"]

        # Set payment type and related entities
        validated_data["payment_type"] = "shopkeeper_to_warehouse"
        validated_data["warehouse"] = order.warehouse
        validated_data["payer"] = request.user  # Shopkeeper
        validated_data["payee"] = order.warehouse.admin  # Warehouse admin
        validated_data["status"] = "pending"

        return super().create(validated_data)


class CreateRiderPayoutSerializer(serializers.ModelSerializer):
    """
    Serializer for warehouse admins to create payouts for riders.
    """

    class Meta:
        model = Payment
        fields = ["order", "rider", "amount", "distance_km", "payment_method", "notes"]

    def validate(self, data):
        """Ensure the order is delivered and the rider is valid."""
        order = data.get("order")
        rider = data.get("rider")

        if order.status != "delivered":
            raise serializers.ValidationError(
                "Payout can only be made for delivered orders."
            )

        if not rider or rider.role != "RIDER":
            raise serializers.ValidationError("Invalid rider selected.")

        # Check if rider already has a payout for this order
        existing_payout = Payment.objects.filter(
            order=order, rider=rider, payment_type="warehouse_to_rider"
        ).exists()

        if existing_payout:
            raise serializers.ValidationError(
                "Payout already exists for this rider and order."
            )

        return data

    def create(self, validated_data):
        request = self.context.get("request")
        order = validated_data["order"]
        rider = validated_data["rider"]

        # Set payment type and related entities
        validated_data["payment_type"] = "warehouse_to_rider"
        validated_data["warehouse"] = order.warehouse
        validated_data["payer"] = order.warehouse.admin  # Warehouse admin
        validated_data["payee"] = rider  # Rider
        validated_data["status"] = "pending"

        return super().create(validated_data)


class UpdatePaymentStatusSerializer(serializers.ModelSerializer):
    """
    Serializer to update payment status (complete or fail a payment).
    """

    class Meta:
        model = Payment
        fields = ["status", "notes"]

    def validate_status(self, value) -> Literal["pending", "completed", "failed"]:
        """Ensure valid status transition."""
        if self.instance.status == "completed":
            raise serializers.ValidationError("Cannot modify a completed payment.")
        if value not in ["pending", "completed", "failed"]:
            raise serializers.ValidationError("Invalid status.")
        return value

    def update(self, instance, validated_data):
        """Update status and set completed_at if status is completed."""
        if (
            validated_data.get("status") == "completed"
            and instance.status != "completed"
        ):
            validated_data["completed_at"] = timezone.now()
        return super().update(instance, validated_data)
