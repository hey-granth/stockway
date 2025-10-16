from rest_framework import serializers
from .models import Item
from warehouses.models import Warehouse
from configs.permissions import IsSuperAdmin


class ItemSerializer(serializers.ModelSerializer):
    """
    Serializer for the Item model.
    - Ensures non-negative quantity
    - Provides helper to check availability for a requested quantity
    """

    available = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Item
        fields = [
            "id",
            "warehouse",
            "name",
            "description",
            "sku",
            "price",
            "quantity",
            "available",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "available"]
        extra_kwargs = {
            "warehouse": {"required": False}
        }

    def validate_quantity(self, value):
        if value is None:
            return value
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        # Enforce that non-super-admins can only create/update items for their own warehouse
        warehouse = attrs.get("warehouse") or getattr(self.instance, "warehouse", None)
        if request and request.user and warehouse:
            if not IsSuperAdmin().has_permission(request, self):
                # request.user must own the warehouse
                if getattr(warehouse, "admin_id", None) != request.user.id:
                    raise serializers.ValidationError({"warehouse": "You do not have permission to manage items for this warehouse."})
        return attrs

    def get_available(self, obj: Item):
        # For now, availability equals current quantity
        return obj.quantity

    def check_requested_availability(self, requested_qty: int) -> bool:
        """Convenience helper to check if requested quantity is available."""
        qty = getattr(self.instance, "quantity", 0)
        return requested_qty <= qty
