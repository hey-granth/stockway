# analytics/serializers.py
from rest_framework import serializers
from .models import AnalyticsSummary


class AnalyticsSummarySerializer(serializers.ModelSerializer):
    """Serializer for analytics summary model."""

    class Meta:
        model = AnalyticsSummary
        fields = ["id", "ref_type", "ref_id", "date", "metrics", "created_at"]
        read_only_fields = ["id", "created_at"]


class SystemAnalyticsSerializer(serializers.Serializer):
    """Serializer for system-wide analytics."""

    date = serializers.DateField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    active_users = serializers.IntegerField()
    average_delivery_time = serializers.FloatField()
    daily_growth = serializers.FloatField()
    pending_orders = serializers.IntegerField(required=False)
    completed_orders = serializers.IntegerField(required=False)
    active_riders = serializers.IntegerField(required=False)
    active_warehouses = serializers.IntegerField(required=False)


class WarehouseAnalyticsSerializer(serializers.Serializer):
    """Serializer for warehouse analytics."""

    warehouse_id = serializers.IntegerField()
    warehouse_name = serializers.CharField()
    total_orders = serializers.IntegerField()
    total_earnings = serializers.DecimalField(max_digits=12, decimal_places=2)
    completion_rate = serializers.FloatField()
    average_delivery_time = serializers.FloatField()
    pending_orders = serializers.IntegerField(required=False)
    active_riders = serializers.IntegerField(required=False)


class RiderAnalyticsSerializer(serializers.Serializer):
    """Serializer for rider analytics."""

    rider_id = serializers.IntegerField()
    rider_name = serializers.CharField()
    completed_deliveries = serializers.IntegerField()
    total_distance = serializers.FloatField()
    total_payout = serializers.DecimalField(max_digits=10, decimal_places=2)
    on_time_delivery_ratio = serializers.FloatField()
    average_delivery_time = serializers.FloatField()


class RiderPersonalAnalyticsSerializer(serializers.Serializer):
    """Serializer for rider's personal analytics."""

    date = serializers.DateField()
    completed_deliveries = serializers.IntegerField()
    total_distance = serializers.FloatField()
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_delivery_time = serializers.FloatField()
    on_time_deliveries = serializers.IntegerField(required=False)
    late_deliveries = serializers.IntegerField(required=False)


class ShopkeeperAnalyticsSerializer(serializers.Serializer):
    """Serializer for shopkeeper analytics."""

    date = serializers.DateField()
    orders_placed = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=12, decimal_places=2)
    most_frequent_warehouse = serializers.CharField(allow_null=True)
    repeat_rate = serializers.FloatField()
    pending_orders = serializers.IntegerField(required=False)
    completed_orders = serializers.IntegerField(required=False)
    cancelled_orders = serializers.IntegerField(required=False)


class WarehousePersonalAnalyticsSerializer(serializers.Serializer):
    """Serializer for warehouse's personal analytics."""

    date = serializers.DateField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    top_items = serializers.ListField(child=serializers.DictField(), required=False)
    avg_delivery_time = serializers.FloatField()
    completion_rate = serializers.FloatField()
    pending_orders = serializers.IntegerField(required=False)
    completed_orders = serializers.IntegerField(required=False)
    rejected_orders = serializers.IntegerField(required=False)

