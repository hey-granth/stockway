
from rest_framework import serializers
from .models import Order, OrderItem
from inventory.models import Item
from warehouses.models import Warehouse
from accounts.models import ShopkeeperProfile


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for the OrderItem model.
    """

    item_name = serializers.CharField(source="item.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "order", "item", "item_name", "quantity", "price"]
        read_only_fields = ["id"]


class OrderItemCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating order items.
    """

    class Meta:
        model = OrderItem
        fields = ["item", "quantity"]


class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new order.
    """

    items = OrderItemCreateSerializer(many=True)

    class Meta:
        model = Order
        fields = ["warehouse", "items"]

    def validate(self, attrs):
        warehouse = attrs.get("warehouse")
        items = attrs.get("items")

        # Check if warehouse exists
        if not Warehouse.objects.filter(id=warehouse.id).exists():
            raise serializers.ValidationError("Warehouse does not exist.")

        # Check inventory for each item
        for item_data in items:
            item = item_data.get("item")
            quantity = item_data.get("quantity")

            try:
                inventory_item = Item.objects.get(id=item.id, warehouse=warehouse)
                if inventory_item.quantity < quantity:
                    raise serializers.ValidationError(
                        f"Not enough stock for {item.name}."
                    )
            except Item.DoesNotExist:
                raise serializers.ValidationError(
                    f"{item.name} not found in this warehouse."
                )

        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        shopkeeper_profile = ShopkeeperProfile.objects.get(
            user=self.context["request"].user
        )
        order = Order.objects.create(
            shopkeeper=shopkeeper_profile.user, **validated_data
        )

        total_amount = 0
        for item_data in items_data:
            item = item_data["item"]
            quantity = item_data["quantity"]
            price = Item.objects.get(id=item.id).price
            total_amount += price * quantity
            OrderItem.objects.create(order=order, item=item, quantity=quantity, price=price)

            # Update inventory
            inventory_item = Item.objects.get(id=item.id)
            inventory_item.quantity -= quantity
            inventory_item.save()

        order.total_amount = total_amount
        order.save()

        return order


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for the Order model.
    """

    order_items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "shopkeeper",
            "warehouse",
            "status",
            "total_amount",
            "order_items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

