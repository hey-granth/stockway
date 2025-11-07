# riders/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Rider, RiderNotification
from warehouses.models import Warehouse

User = get_user_model()


class RiderSerializer(serializers.ModelSerializer):
    """
    Serializer for Rider model with detailed information.
    """

    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    warehouse_id = serializers.IntegerField(source="warehouse.id", read_only=True)
    rider_name = serializers.CharField(source="user.full_name", read_only=True)
    rider_email = serializers.CharField(source="user.email", read_only=True)
    latitude = serializers.FloatField(read_only=True)
    longitude = serializers.FloatField(read_only=True)

    class Meta:
        model = Rider
        fields = [
            "id",
            "user",
            "warehouse",
            "warehouse_id",
            "warehouse_name",
            "rider_name",
            "rider_email",
            "status",
            "current_location",
            "latitude",
            "longitude",
            "total_earnings",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "total_earnings", "created_at", "updated_at"]


class RiderRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for rider registration (admin/super_admin only).
    """

    user_id = serializers.IntegerField(write_only=True)
    warehouse_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Rider
        fields = ["user_id", "warehouse_id", "status"]

    def validate_user_id(self, value):
        """Validate that the user exists and has RIDER role"""
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")

        if user.role != "RIDER":
            raise serializers.ValidationError("User must have RIDER role")

        # Check if rider profile already exists
        if hasattr(user, "rider_profile"):
            raise serializers.ValidationError(
                "Rider profile already exists for this user"
            )

        return value

    def validate_warehouse_id(self, value):
        """Validate that the warehouse exists"""
        try:
            Warehouse.objects.get(id=value)
        except Warehouse.DoesNotExist:
            raise serializers.ValidationError("Warehouse not found")

        return value

    def validate(self, attrs):
        """Validate warehouse ownership for warehouse_admin"""
        request = self.context.get("request")
        warehouse_id = attrs.get("warehouse_id")

        if request and request.user.role == "WAREHOUSE_MANAGER":
            # Warehouse admin can only register riders to their own warehouse
            warehouse = Warehouse.objects.get(id=warehouse_id)
            if warehouse.admin != request.user:
                raise serializers.ValidationError(
                    "You can only register riders to your own warehouse"
                )

        return attrs

    def create(self, validated_data):
        """Create rider profile"""
        user = User.objects.get(id=validated_data.pop("user_id"))
        warehouse = Warehouse.objects.get(id=validated_data.pop("warehouse_id"))

        rider = Rider.objects.create(user=user, warehouse=warehouse, **validated_data)
        return rider


class RiderProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for rider's own profile view.
    """

    name = serializers.CharField(source="user.full_name", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    warehouse_address = serializers.CharField(
        source="warehouse.address", read_only=True
    )
    latitude = serializers.FloatField(read_only=True)
    longitude = serializers.FloatField(read_only=True)

    class Meta:
        model = Rider
        fields = [
            "id",
            "name",
            "email",
            "warehouse_name",
            "warehouse_address",
            "status",
            "current_location",
            "latitude",
            "longitude",
            "total_earnings",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "name",
            "email",
            "warehouse_name",
            "warehouse_address",
            "total_earnings",
            "created_at",
        ]


class RiderLocationUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating rider location.
    """

    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)

    def validate(self, attrs):
        """Validate coordinates"""
        lat = attrs.get("latitude")
        lng = attrs.get("longitude")

        if lat is None or lng is None:
            raise serializers.ValidationError(
                "Both latitude and longitude are required"
            )

        return attrs


class RiderListSerializer(serializers.ModelSerializer):
    """
    Compact serializer for rider list view.
    """

    name = serializers.CharField(source="user.full_name", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    active_orders_count = serializers.SerializerMethodField()

    class Meta:
        model = Rider
        fields = [
            "id",
            "name",
            "email",
            "status",
            "active_orders_count",
            "total_earnings",
        ]

    def get_active_orders_count(self, obj):
        """Get count of active orders for this rider"""
        from orders.models import Order

        return Order.objects.filter(
            delivery__rider=obj.user,
            status__in=["assigned", "in_transit"],
        ).count()


class RiderEarningsSerializer(serializers.Serializer):
    """Serializer for rider earnings summary"""
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    completed_orders_count = serializers.IntegerField()
    total_distance_km = serializers.DecimalField(max_digits=10, decimal_places=2)


class RiderHistorySerializer(serializers.Serializer):
    """Serializer for rider delivery history"""
    order_id = serializers.IntegerField()
    warehouse_name = serializers.CharField()
    warehouse_id = serializers.IntegerField()
    distance_km = serializers.DecimalField(max_digits=10, decimal_places=2)
    payout_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    delivery_date = serializers.DateTimeField()
    status = serializers.CharField()


class RiderPerformanceSerializer(serializers.Serializer):
    """Serializer for rider performance metrics"""
    average_delivery_time_minutes = serializers.FloatField(allow_null=True)
    success_rate = serializers.FloatField()
    total_deliveries = serializers.IntegerField()
    successful_deliveries = serializers.IntegerField()
    distance_per_order = serializers.FloatField()
    total_distance_km = serializers.FloatField()
    monthly_aggregates = serializers.ListField(required=False)


class RiderNotificationSerializer(serializers.ModelSerializer):
    """Serializer for rider notifications"""

    class Meta:
        model = RiderNotification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'is_read',
            'metadata',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RiderAvailabilitySerializer(serializers.Serializer):
    """Serializer for updating rider availability"""
    availability = serializers.ChoiceField(choices=['available', 'off-duty'])


class ActiveRiderSerializer(serializers.Serializer):
    """Serializer for active riders with live location"""
    rider_id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    last_update = serializers.DateTimeField()
    status = serializers.CharField()


class WarehouseRiderMetricsSerializer(serializers.Serializer):
    """Serializer for warehouse-level rider metrics"""
    rider_id = serializers.IntegerField()
    rider_name = serializers.CharField()
    rider_email = serializers.CharField()
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    completed_orders = serializers.IntegerField()
    total_distance_km = serializers.DecimalField(max_digits=10, decimal_places=2)
    success_rate = serializers.FloatField()
    average_delivery_time_minutes = serializers.FloatField(allow_null=True)
    status = serializers.CharField()
    availability = serializers.CharField()


class RiderManagementSerializer(serializers.Serializer):
    """Serializer for admin rider management actions"""
    action = serializers.ChoiceField(choices=['suspend', 'reactivate', 'reassign'])
    rider_id = serializers.IntegerField()
    reason = serializers.CharField(required=False, allow_blank=True)
    new_warehouse_id = serializers.IntegerField(required=False)


