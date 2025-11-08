from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model"""

    class Meta:
        model = Notification
        fields = ["id", "title", "message", "type", "is_read", "created_at"]
        read_only_fields = ["id", "created_at"]


class MarkAsReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read"""

    notification_id = serializers.IntegerField(required=False, allow_null=True)
    mark_all = serializers.BooleanField(default=False)

    def validate(self, attrs):
        """Ensure either notification_id or mark_all is provided"""
        if not attrs.get("mark_all") and not attrs.get("notification_id"):
            raise serializers.ValidationError(
                "Either 'notification_id' or 'mark_all' must be provided"
            )
        return attrs

