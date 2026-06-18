from rest_framework import serializers
from .models import Warehouse, WarehouseNotification, RiderPayout


class WarehouseSerializer(serializers.ModelSerializer):
    """Serializer for Warehouse model"""

    admin_email = serializers.EmailField(source="admin.email", read_only=True)
    admin_name = serializers.CharField(source="admin.full_name", read_only=True)
    latitude = serializers.FloatField(write_only=True, required=False)
    longitude = serializers.FloatField(write_only=True, required=False)
    total_items = serializers.SerializerMethodField(read_only=True)
    low_stock_items_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Warehouse
        fields = [
            "id",
            "admin",
            "admin_email",
            "admin_name",
            "name",
            "address",
            "contact_number",
            "latitude",
            "longitude",
            "location",
            "is_active",
            "is_approved",
            "total_items",
            "low_stock_items_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "admin", "location", "created_at", "updated_at"]

    def get_total_items(self, obj):
        return (
            obj.items.filter(is_active=True).count()
            if hasattr(obj.items.model, "is_active")
            else obj.items.count()
        )

    def get_low_stock_items_count(self, obj):
        # The Item model doesn't have low_stock_threshold, so we'll use a default threshold
        threshold = 10
        return obj.items.filter(quantity__lte=threshold).count()

    def create(self, validated_data):
        latitude = validated_data.pop("latitude", None)
        longitude = validated_data.pop("longitude", None)

        warehouse = Warehouse(**validated_data)
        if latitude is not None and longitude is not None:
            warehouse.set_coordinates(latitude, longitude)
        warehouse.save()
        return warehouse

    def update(self, instance, validated_data):
        latitude = validated_data.pop("latitude", None)
        longitude = validated_data.pop("longitude", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if latitude is not None and longitude is not None:
            instance.set_coordinates(latitude, longitude)

        instance.save()
        return instance


class WarehouseListSerializer(serializers.ModelSerializer):
    """Simplified serializer for warehouse list view"""

    admin_email = serializers.EmailField(source="admin.email", read_only=True)
    admin_name = serializers.CharField(source="admin.full_name", read_only=True)
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = Warehouse
        fields = [
            "id",
            "admin",
            "admin_email",
            "admin_name",
            "name",
            "address",
            "contact_number",
            "latitude",
            "longitude",
            "is_active",
            "is_approved",
            "created_at",
        ]

    def get_latitude(self, obj):
        return obj.latitude

    def get_longitude(self, obj):
        return obj.longitude


class WarehouseNotificationSerializer(serializers.ModelSerializer):
    """Serializer for warehouse notifications"""

    class Meta:
        model = WarehouseNotification
        fields = [
            "id",
            "warehouse",
            "notification_type",
            "title",
            "message",
            "is_read",
            "metadata",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class RiderPayoutSerializer(serializers.ModelSerializer):
    """Serializer for rider payouts"""

    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    rider_name = serializers.CharField(source="rider.user.full_name", read_only=True)
    rider_email = serializers.EmailField(source="rider.user.email", read_only=True)

    class Meta:
        model = RiderPayout
        fields = [
            "id",
            "warehouse",
            "warehouse_name",
            "rider",
            "rider_name",
            "rider_email",
            "order",
            "base_rate",
            "distance_km",
            "distance_rate",
            "total_amount",
            "status",
            "payment_reference",
            "created_at",
            "paid_at",
        ]
        read_only_fields = ["id", "total_amount", "created_at"]


# Import models for serializer methods
