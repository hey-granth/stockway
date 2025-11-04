# shopkeepers/views.py
from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from django.contrib.gis.db.models.functions import Distance as DistanceFunc
from django.contrib.gis.measure import Distance
from datetime import timedelta
from decimal import Decimal
import calendar
from core.permissions import IsShopkeeper
from .models import Notification, SupportTicket
from .serializers import (
    OrderDetailSerializer,
    OrderCreateSerializer,
    OrderUpdateSerializer,
    PaymentRecordSerializer,
    PaymentSummarySerializer,
    InventoryItemSerializer,
    NotificationSerializer,
    NotificationMarkReadSerializer,
    SupportTicketSerializer,
    SupportTicketCreateSerializer,
    AnalyticsSummarySerializer,
)
from orders.models import Order
from payments.models import Payment
from inventory.models import Item
from warehouses.models import Warehouse
from accounts.models import ShopkeeperProfile


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination class."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


# ===== Order Management Views =====


class ShopkeeperOrderCreateView(generics.CreateAPIView):
    """
    Create a new order.

    POST /api/shopkeeper/orders/create/
    Body: {
        "warehouse": <warehouse_id>,
        "items": [
            {"item_id": <id>, "quantity": <qty>},
            ...
        ]
    }
    """

    serializer_class = OrderCreateSerializer
    permission_classes = [IsAuthenticated, IsShopkeeper]

    def get_serializer_context(self):
        return {"request": self.request}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        # Create notification for order creation
        Notification.objects.create(
            user=request.user,
            notification_type="general",
            title="Order Created",
            message=f"Your order #{order.id} has been created successfully.",
            order=order,
        )

        return Response(
            OrderDetailSerializer(order).data, status=status.HTTP_201_CREATED
        )


class ShopkeeperOrderListView(generics.ListAPIView):
    """
    List all orders for the authenticated shopkeeper.

    GET /api/shopkeeper/orders/
    Query params: ?status=pending&ordering=-created_at
    """

    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated, IsShopkeeper]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at", "updated_at", "total_amount", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = (
            Order.objects.filter(shopkeeper=self.request.user)
            .select_related("warehouse", "delivery", "delivery__rider")
            .prefetch_related("order_items__item")
        )

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by date range
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset


class ShopkeeperOrderDetailView(generics.RetrieveAPIView):
    """
    Get details of a specific order.

    GET /api/shopkeeper/orders/<id>/
    """

    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated, IsShopkeeper]

    def get_queryset(self):
        return (
            Order.objects.filter(shopkeeper=self.request.user)
            .select_related("warehouse", "delivery", "delivery__rider")
            .prefetch_related("order_items__item")
        )


class ShopkeeperOrderUpdateView(generics.UpdateAPIView):
    """
    Update order status (cancel only).

    PATCH /api/shopkeeper/orders/<id>/update/
    Body: {"status": "cancelled"}
    """

    serializer_class = OrderUpdateSerializer
    permission_classes = [IsAuthenticated, IsShopkeeper]

    def get_queryset(self):
        return Order.objects.filter(shopkeeper=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Create notification for order cancellation
        Notification.objects.create(
            user=request.user,
            notification_type="order_cancelled",
            title="Order Cancelled",
            message=f"Your order #{instance.id} has been cancelled.",
            order=instance,
        )

        return Response(OrderDetailSerializer(instance).data)


class ShopkeeperOrderTrackingView(APIView):
    """
    Get current order status and assigned rider info.

    GET /api/shopkeeper/orders/<id>/tracking/
    """

    permission_classes = [IsAuthenticated, IsShopkeeper]

    def get(self, request, pk):
        try:
            order = Order.objects.select_related(
                "warehouse", "delivery", "delivery__rider"
            ).get(id=pk, shopkeeper=request.user)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND
            )

        tracking_data = {
            "order_id": order.id,
            "order_status": order.status,
            "order_status_display": order.get_status_display(),
            "total_amount": str(order.total_amount),
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "warehouse": {
                "id": order.warehouse.id,
                "name": order.warehouse.name,
                "address": order.warehouse.address,
            },
            "delivery": None,
            "rider": None,
        }

        # Add delivery and rider info if available
        try:
            delivery = order.delivery
            tracking_data["delivery"] = {
                "status": delivery.status,
                "status_display": delivery.get_status_display(),
                "delivery_fee": str(delivery.delivery_fee),
                "created_at": delivery.created_at,
                "updated_at": delivery.updated_at,
            }

            if delivery.rider:
                tracking_data["rider"] = {
                    "id": delivery.rider.id,
                    "phone_number": delivery.rider.phone_number,
                }
        except Exception:
            pass

        return Response(tracking_data, status=status.HTTP_200_OK)


# ===== Payment Records Views =====


class ShopkeeperPaymentListView(generics.ListAPIView):
    """
    List payment transaction history.

    GET /api/shopkeeper/payments/
    Query params: ?status=completed&ordering=-created_at
    """

    serializer_class = PaymentRecordSerializer
    permission_classes = [IsAuthenticated, IsShopkeeper]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at", "amount", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = Payment.objects.filter(
            payer=self.request.user, payment_type="shopkeeper_to_warehouse"
        ).select_related("order", "warehouse")

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by date range
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset


class ShopkeeperPaymentSummaryView(APIView):
    """
    Get payment summary with pending dues.

    GET /api/shopkeeper/payments/summary/
    """

    permission_classes = [IsAuthenticated, IsShopkeeper]

    def get(self, request):
        payments = Payment.objects.filter(
            payer=request.user, payment_type="shopkeeper_to_warehouse"
        )

        summary = payments.aggregate(
            total_paid=Sum("amount", filter=Q(status="completed")) or Decimal("0.00"),
            total_pending=Sum("amount", filter=Q(status="pending")) or Decimal("0.00"),
            total_failed=Sum("amount", filter=Q(status="failed")) or Decimal("0.00"),
            pending_count=Count("id", filter=Q(status="pending")),
            completed_count=Count("id", filter=Q(status="completed")),
        )

        response_data = {
            "total_paid": summary["total_paid"] or Decimal("0.00"),
            "total_pending": summary["total_pending"] or Decimal("0.00"),
            "total_failed": summary["total_failed"] or Decimal("0.00"),
            "pending_orders_count": summary["pending_count"],
            "completed_payments_count": summary["completed_count"],
        }

        serializer = PaymentSummarySerializer(response_data)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ===== Inventory Browsing Views =====


class ShopkeeperInventoryBrowseView(generics.ListAPIView):
    """
    Browse inventory from nearby warehouses with filters.

    GET /api/shopkeeper/inventory/browse/
    Query params: ?warehouse=<id>&search=<name>&min_price=<price>&max_price=<price>&in_stock=true
    """

    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated, IsShopkeeper]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description", "sku"]
    ordering_fields = ["name", "price", "quantity", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        queryset = Item.objects.select_related("warehouse").all()

        # Filter by warehouse
        warehouse_id = self.request.query_params.get("warehouse")
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)

        # Filter by price range
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # Filter by stock availability
        in_stock = self.request.query_params.get("in_stock")
        if in_stock and in_stock.lower() == "true":
            queryset = queryset.filter(quantity__gt=0)

        return queryset


class ShopkeeperNearbyWarehousesView(APIView):
    """
    Get nearby warehouses based on shopkeeper location.

    GET /api/shopkeeper/warehouses/nearby/
    Query params: ?radius=10 (in kilometers)
    """

    permission_classes = [IsAuthenticated, IsShopkeeper]

    def get(self, request):
        try:
            profile = ShopkeeperProfile.objects.get(user=request.user)
        except ShopkeeperProfile.DoesNotExist:
            return Response(
                {"error": "Shopkeeper profile not found. Please complete onboarding."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not profile.location:
            return Response(
                {
                    "error": "Location not set. Please update your profile with location."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get radius from query params (default 10km)
        radius = float(request.query_params.get("radius", 10))

        # Find nearby warehouses using PostGIS
        nearby_warehouses = (
            Warehouse.objects.filter(
                location__distance_lte=(profile.location, Distance(km=radius)),
                location__isnull=False,
            )
            .annotate(distance=DistanceFunc("location", profile.location))
            .order_by("distance")
        )

        warehouses_data = [
            {
                "id": w.id,
                "name": w.name,
                "address": w.address,
                "distance_km": round(w.distance.km, 2)
                if hasattr(w, "distance")
                else None,
                "latitude": float(w.latitude) if w.latitude else None,
                "longitude": float(w.longitude) if w.longitude else None,
            }
            for w in nearby_warehouses
        ]

        return Response({"warehouses": warehouses_data}, status=status.HTTP_200_OK)


# ===== Notification Views =====


class ShopkeeperNotificationListView(generics.ListAPIView):
    """
    List all notifications for the shopkeeper.

    GET /api/shopkeeper/notifications/
    Query params: ?is_read=false
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, IsShopkeeper]
    pagination_class = StandardResultsSetPagination
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)

        # Filter by read status
        is_read = self.request.query_params.get("is_read")
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == "true")

        return queryset


class ShopkeeperNotificationMarkReadView(APIView):
    """
    Mark notifications as read.

    POST /api/shopkeeper/notifications/mark-read/
    Body: {"notification_ids": [1, 2, 3]} or {} to mark all as read
    """

    permission_classes = [IsAuthenticated, IsShopkeeper]

    def post(self, request):
        serializer = NotificationMarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        notification_ids = serializer.validated_data.get("notification_ids")

        if notification_ids:
            # Mark specific notifications as read
            updated_count = Notification.objects.filter(
                user=request.user, id__in=notification_ids, is_read=False
            ).update(is_read=True)
        else:
            # Mark all unread notifications as read
            updated_count = Notification.objects.filter(
                user=request.user, is_read=False
            ).update(is_read=True)

        return Response(
            {"message": f"{updated_count} notification(s) marked as read."},
            status=status.HTTP_200_OK,
        )


class ShopkeeperNotificationUnreadCountView(APIView):
    """
    Get count of unread notifications.

    GET /api/shopkeeper/notifications/unread-count/
    """

    permission_classes = [IsAuthenticated, IsShopkeeper]

    def get(self, request):
        unread_count = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()

        return Response({"unread_count": unread_count}, status=status.HTTP_200_OK)


# ===== Support/Feedback Views =====


class ShopkeeperSupportTicketListView(generics.ListAPIView):
    """
    List all support tickets created by the shopkeeper.

    GET /api/shopkeeper/support/tickets/
    Query params: ?status=open&category=order_issue
    """

    serializer_class = SupportTicketSerializer
    permission_classes = [IsAuthenticated, IsShopkeeper]
    pagination_class = StandardResultsSetPagination
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = SupportTicket.objects.filter(user=self.request.user)

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by category
        category_filter = self.request.query_params.get("category")
        if category_filter:
            queryset = queryset.filter(category=category_filter)

        return queryset


class ShopkeeperSupportTicketCreateView(generics.CreateAPIView):
    """
    Create a new support ticket.

    POST /api/shopkeeper/support/tickets/create/
    Body: {
        "category": "order_issue",
        "subject": "Problem with order",
        "description": "Details...",
        "order": <order_id> (optional)
    }
    """

    serializer_class = SupportTicketCreateSerializer
    permission_classes = [IsAuthenticated, IsShopkeeper]

    def get_serializer_context(self):
        return {"request": self.request}


class ShopkeeperSupportTicketDetailView(generics.RetrieveAPIView):
    """
    Get details of a specific support ticket.

    GET /api/shopkeeper/support/tickets/<id>/
    """

    serializer_class = SupportTicketSerializer
    permission_classes = [IsAuthenticated, IsShopkeeper]

    def get_queryset(self):
        return SupportTicket.objects.filter(user=self.request.user)


# ===== Analytics Views =====


class ShopkeeperAnalyticsView(APIView):
    """
    Get analytics summary with monthly breakdown.

    GET /api/shopkeeper/analytics/
    Query params: ?months=6 (default 6 months)
    """

    permission_classes = [IsAuthenticated, IsShopkeeper]

    def get(self, request):
        # Get number of months to analyze (default 6)
        months_count = int(request.query_params.get("months", 6))

        # Get all orders for the shopkeeper
        orders = Order.objects.filter(shopkeeper=request.user)

        # Overall summary
        overall_stats = orders.aggregate(
            total_orders=Count("id"),
            total_spending=Sum("total_amount") or Decimal("0.00"),
            pending_orders=Count("id", filter=Q(status="pending")),
            completed_orders=Count("id", filter=Q(status="delivered")),
            cancelled_orders=Count("id", filter=Q(status="cancelled")),
            avg_order_value=Avg("total_amount") or Decimal("0.00"),
        )

        # Monthly breakdown
        monthly_data = []
        today = timezone.now()

        for i in range(months_count):
            # Calculate month and year
            month_date = today - timedelta(days=30 * i)
            month = month_date.month
            year = month_date.year
            month_name = calendar.month_name[month]

            # Filter orders for this month
            month_orders = orders.filter(created_at__year=year, created_at__month=month)

            month_stats = month_orders.aggregate(
                total_orders=Count("id"),
                completed_orders=Count("id", filter=Q(status="delivered")),
                cancelled_orders=Count("id", filter=Q(status="cancelled")),
                total_spending=Sum("total_amount") or Decimal("0.00"),
                avg_order_value=Avg("total_amount") or Decimal("0.00"),
            )

            monthly_data.append(
                {
                    "month": month_name,
                    "year": year,
                    "total_orders": month_stats["total_orders"],
                    "completed_orders": month_stats["completed_orders"],
                    "cancelled_orders": month_stats["cancelled_orders"],
                    "total_spending": month_stats["total_spending"],
                    "average_order_value": month_stats["avg_order_value"],
                }
            )

        response_data = {
            "total_orders": overall_stats["total_orders"],
            "total_spending": overall_stats["total_spending"],
            "pending_orders": overall_stats["pending_orders"],
            "completed_orders": overall_stats["completed_orders"],
            "cancelled_orders": overall_stats["cancelled_orders"],
            "average_order_value": overall_stats["avg_order_value"],
            "monthly_data": monthly_data,
        }

        serializer = AnalyticsSummarySerializer(response_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
