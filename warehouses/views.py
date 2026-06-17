from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Sum
from django_filters.rest_framework import DjangoFilterBackend
import csv
from django.http import HttpResponse

from .models import Warehouse, WarehouseNotification, RiderPayout
from .serializers import (
    WarehouseSerializer,
    WarehouseListSerializer,
    WarehouseNotificationSerializer,
    RiderPayoutSerializer,
)
from .permissions import IsWarehouseAdminOrReadOnly
from inventory.models import Item
from inventory.serializers import ItemSerializer
from orders.models import Order
from orders.serializers import OrderSerializer, OrderListSerializer
from riders.models import Rider
from .geo_services import find_nearest_available_rider


class WarehouseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for warehouse profile management.

    Provides CRUD operations for warehouses with role-based filtering.
    """

    queryset = Warehouse.objects.all()
    permission_classes = [IsAuthenticated, IsWarehouseAdminOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["is_active", "is_approved"]
    search_fields = ["name", "address", "contact_number"]
    ordering_fields = ["created_at", "name", "updated_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return WarehouseListSerializer
        return WarehouseSerializer

    def get_queryset(self):
        """Filter warehouses based on user role"""
        user = self.request.user
        if user.role == "admin":
            return Warehouse.objects.all()
        elif user.role == "warehouse":
            return Warehouse.objects.filter(admin=user)
        else:
            # Shopkeepers and riders see only active and approved warehouses
            return Warehouse.objects.filter(is_active=True, is_approved=True)

    def perform_create(self, serializer):
        """Set current user as warehouse admin"""
        serializer.save(admin=self.request.user)

    @action(detail=True, methods=["get"], url_path="inventory")
    def inventory(self, request, pk=None):
        """List inventory items for a warehouse"""
        warehouse = self.get_object()
        items = Item.objects.filter(warehouse=warehouse)

        # Apply filters
        search = request.query_params.get("search")
        if search:
            items = items.filter(Q(name__icontains=search) | Q(sku__icontains=search))

        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="inventory/bulk-update")
    def bulk_update_inventory(self, request, pk=None):
        """Bulk update inventory stock levels"""
        warehouse = self.get_object()
        updates = request.data.get("updates", [])

        if not isinstance(updates, list):
            return Response(
                {"error": "updates must be a list"}, status=status.HTTP_400_BAD_REQUEST
            )

        results = []

        for update in updates:
            item_id = update.get("item_id")
            quantity_change = update.get("quantity_change")

            if not item_id or quantity_change is None:
                results.append(
                    {
                        "item_id": item_id,
                        "success": False,
                        "error": "item_id and quantity_change are required",
                    }
                )
                continue

            try:
                item = Item.objects.get(id=item_id, warehouse=warehouse)
                new_quantity = item.quantity + quantity_change

                if new_quantity < 0:
                    results.append(
                        {
                            "item_id": item_id,
                            "success": False,
                            "error": "Stock quantity cannot be negative",
                        }
                    )
                    continue

                item.quantity = new_quantity
                item.save()

                results.append(
                    {"item_id": item_id, "success": True, "new_quantity": item.quantity}
                )
            except Item.DoesNotExist:
                results.append(
                    {"item_id": item_id, "success": False, "error": "Item not found"}
                )
            except Exception as e:
                results.append({"item_id": item_id, "success": False, "error": str(e)})

        return Response({"message": "Bulk update completed", "results": results})

    @action(detail=True, methods=["get"], url_path="orders")
    def orders(self, request, pk=None):
        """List orders for a warehouse"""
        warehouse = self.get_object()
        orders = Order.objects.filter(warehouse=warehouse).annotate(
            items_count=Count("order_items")
        )

        # Apply filters
        status_filter = request.query_params.get("status")
        if status_filter:
            orders = orders.filter(status=status_filter)

        from_date = request.query_params.get("from_date")
        if from_date:
            orders = orders.filter(created_at__date__gte=from_date)

        to_date = request.query_params.get("to_date")
        if to_date:
            orders = orders.filter(created_at__date__lte=to_date)

        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="orders/(?P<order_id>[^/.]+)")
    def order_detail(self, request, order_id=None, pk=None):
        """Get detailed order information"""
        order = get_object_or_404(Order, id=order_id)

        # Check permissions
        if request.user.role not in ["admin"]:
            if (
                hasattr(request.user, "warehouses")
                and order.warehouse not in request.user.warehouses.all()
            ):
                if not (
                    hasattr(request.user, "rider_profile")
                    and order.rider == request.user.rider_profile
                ):
                    return Response(
                        {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
                    )

        serializer = OrderSerializer(order)
        return Response(serializer.data)

    @action(
        detail=False, methods=["post"], url_path="orders/(?P<order_id>[^/.]+)/action"
    )
    def order_action(self, request, order_id=None, pk=None):
        """Accept or reject an order"""
        order = get_object_or_404(Order, id=order_id)

        # Check if user is warehouse admin
        if order.warehouse.admin != request.user and request.user.role != "ADMIN":
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        action_type = request.data.get("action")
        if action_type not in ["accept", "reject"]:
            return Response(
                {"error": 'Invalid action. Must be "accept" or "reject"'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order.status != "pending":
            return Response(
                {"error": f"Only pending orders can be {action_type}ed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action_type == "accept":
            order.status = "accepted"
            order.save()
            message = "Order accepted successfully"
        else:  # reject
            rejection_reason = request.data.get("rejection_reason", "")
            if not rejection_reason:
                return Response(
                    {"error": "Rejection reason is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            order.status = "rejected"
            # Store rejection reason in notes or a custom field if it exists
            if hasattr(order, "rejection_reason"):
                order.rejection_reason = rejection_reason
            order.save()
            message = "Order rejected"

        return Response({"message": message, "order": OrderSerializer(order).data})

    @action(
        detail=False,
        methods=["post"],
        url_path="orders/(?P<order_id>[^/.]+)/assign-rider",
    )
    def assign_rider(self, request, order_id=None, pk=None):
        """Manually assign a rider to an order"""
        order = get_object_or_404(Order, id=order_id)

        # Check permissions
        if order.warehouse.admin != request.user and request.user.role != "ADMIN":
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        rider_id = request.data.get("rider_id")
        if not rider_id:
            return Response(
                {"error": "rider_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        rider = get_object_or_404(Rider, id=rider_id)

        if order.status not in ["accepted", "pending"]:
            return Response(
                {"error": "Only accepted or pending orders can have riders assigned"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Assign rider to order if the field exists
        if hasattr(order, "rider"):
            order.rider = rider
            order.status = "in_transit"
            order.save()

            return Response(
                {
                    "message": "Rider assigned successfully",
                    "order": OrderSerializer(order).data,
                }
            )
        else:
            return Response(
                {"error": "Order model does not support rider assignment"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=False,
        methods=["post"],
        url_path="orders/(?P<order_id>[^/.]+)/auto-assign-rider",
    )
    def auto_assign_rider(self, request, order_id=None, pk=None):
        """Automatically assign the nearest available rider"""
        order = get_object_or_404(Order, id=order_id)

        # Check permissions
        if order.warehouse.admin != request.user and request.user.role != "ADMIN":
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        # Find nearest rider
        rider = find_nearest_available_rider(order.warehouse)

        if not rider:
            return Response(
                {"error": "No available riders found nearby"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if order.status not in ["accepted", "pending"]:
            return Response(
                {"error": "Only accepted or pending orders can have riders assigned"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Assign rider to order if the field exists
        if hasattr(order, "rider"):
            order.rider = rider
            order.status = "in_transit"
            order.save()

            return Response(
                {
                    "message": "Rider auto-assigned successfully",
                    "order": OrderSerializer(order).data,
                }
            )
        else:
            return Response(
                {"error": "Order model does not support rider assignment"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["get"], url_path="deliveries")
    def deliveries(self, request, pk=None):
        """Track deliveries and assigned riders"""
        warehouse = self.get_object()

        # Get active deliveries by default
        status_filter = request.query_params.get("status", "active")

        if status_filter == "active":
            orders = Order.objects.filter(
                warehouse=warehouse, status__in=["assigned", "picked_up", "in_transit"]
            ).annotate(items_count=Count("order_items"))
        else:
            orders = Order.objects.filter(
                warehouse=warehouse, status=status_filter
            ).annotate(items_count=Count("order_items"))

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="notifications")
    def notifications(self, request, pk=None):
        """Get warehouse notifications"""
        warehouse = self.get_object()
        notifications = WarehouseNotification.objects.filter(warehouse=warehouse)

        # Apply filters
        is_read = request.query_params.get("is_read")
        if is_read:
            notifications = notifications.filter(is_read=is_read.lower() == "true")

        notif_type = request.query_params.get("type")
        if notif_type:
            notifications = notifications.filter(notification_type=notif_type)

        serializer = WarehouseNotificationSerializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="notifications/mark-read")
    def mark_notifications_read(self, request, pk=None):
        """Mark multiple notifications as read"""
        warehouse = self.get_object()
        notification_ids = request.data.get("notification_ids", [])

        count = WarehouseNotification.objects.filter(
            warehouse=warehouse, id__in=notification_ids
        ).update(is_read=True)

        return Response({"message": f"Marked {count} notifications as read"})

    @action(detail=True, methods=["get"], url_path="rider-payouts")
    def rider_payouts(self, request, pk=None):
        """List rider payouts"""
        warehouse = self.get_object()
        payouts = RiderPayout.objects.filter(warehouse=warehouse)

        # Apply filters
        status_filter = request.query_params.get("status")
        if status_filter:
            payouts = payouts.filter(status=status_filter)

        serializer = RiderPayoutSerializer(payouts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="analytics/summary")
    def analytics_summary(self, request, pk=None):
        """Get comprehensive analytics summary"""
        warehouse = self.get_object()

        # Get date filters
        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")

        orders = Order.objects.filter(warehouse=warehouse)
        if from_date:
            orders = orders.filter(created_at__date__gte=from_date)
        if to_date:
            orders = orders.filter(created_at__date__lte=to_date)

        # Calculate statistics
        total_orders = orders.count()
        completed_orders = orders.filter(status="delivered").count()
        pending_orders = orders.filter(status="pending").count()
        total_revenue = (
            orders.filter(status="delivered").aggregate(total=Sum("total_amount"))[
                "total"
            ]
            or 0
        )

        # Get top items by stock
        from inventory.models import Item

        top_items = (
            Item.objects.filter(warehouse=warehouse)
            .order_by("-quantity")[:5]
            .values("name", "sku", "quantity")
        )

        # Get low stock items (using threshold of 10)
        low_stock_threshold = 10
        low_stock_items = Item.objects.filter(
            warehouse=warehouse, quantity__lte=low_stock_threshold
        ).values("name", "sku", "quantity")

        return Response(
            {
                "total_orders": total_orders,
                "completed_orders": completed_orders,
                "pending_orders": pending_orders,
                "total_revenue": str(total_revenue),
                "top_items": list(top_items),
                "low_stock_items": list(low_stock_items),
            }
        )

    @action(detail=True, methods=["get"], url_path="analytics/export")
    def export_analytics(self, request, pk=None):
        """Export analytics data in CSV or JSON format"""
        warehouse = self.get_object()
        export_format = request.query_params.get("format", "json")

        # Get date filters
        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")

        orders = Order.objects.filter(warehouse=warehouse).select_related("shopkeeper")
        if from_date:
            orders = orders.filter(created_at__date__gte=from_date)
        if to_date:
            orders = orders.filter(created_at__date__lte=to_date)

        if export_format == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = (
                f'attachment; filename="warehouse_{warehouse.id}_analytics.csv"'
            )

            writer = csv.writer(response)
            writer.writerow(
                ["Order ID", "Status", "Amount", "Date", "Shopkeeper", "Rider"]
            )

            for order in orders:
                rider_email = ""
                if hasattr(order, "rider") and order.rider:
                    rider_email = (
                        order.rider.user.email
                        if hasattr(order.rider, "user")
                        else str(order.rider)
                    )

                writer.writerow(
                    [
                        order.id,
                        order.status,
                        str(order.total_amount),
                        order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        order.shopkeeper.email
                        if hasattr(order.shopkeeper, "email")
                        else str(order.shopkeeper),
                        rider_email,
                    ]
                )

            return response
        else:  # JSON
            order_data = []
            for order in orders:
                rider_email = None
                if hasattr(order, "rider") and order.rider:
                    rider_email = (
                        order.rider.user.email
                        if hasattr(order.rider, "user")
                        else str(order.rider)
                    )

                order_data.append(
                    {
                        "id": order.id,
                        "status": order.status,
                        "total_amount": str(order.total_amount),
                        "created_at": order.created_at.isoformat(),
                        "shopkeeper_email": order.shopkeeper.email
                        if hasattr(order.shopkeeper, "email")
                        else str(order.shopkeeper),
                        "rider_email": rider_email,
                    }
                )

            data = {
                "warehouse_id": warehouse.id,
                "warehouse_name": warehouse.name,
                "orders": order_data,
            }
            return Response(data)
