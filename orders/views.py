# orders/views.py
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Prefetch
from django.db import transaction
from .models import Order, OrderItem
from .serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    OrderListSerializer,
    OrderAssignmentSerializer,
)
from delivery.models import Delivery
from core.permissions import IsShopkeeper, IsWarehouseAdmin, IsRider
from core.throttling import OrderCreationThrottle
from core.order_state import OrderStateManager
from core.validators import IDValidator, StringValidator
import logging

logger = logging.getLogger(__name__)


class OrderCreateView(APIView):
    """
    POST /api/shopkeeper/orders/create/
    Create a new order (shopkeeper only)
    """

    permission_classes = [permissions.IsAuthenticated, IsShopkeeper]
    throttle_classes = [OrderCreationThrottle]

    def post(self, request):
        serializer = OrderCreateSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            try:
                order = serializer.save()

                # Fetch the created order with related data
                order = (
                    Order.objects.select_related("shopkeeper", "warehouse")
                    .prefetch_related(
                        Prefetch(
                            "order_items",
                            queryset=OrderItem.objects.select_related("item"),
                        )
                    )
                    .get(id=order.id)
                )

                response_serializer = OrderSerializer(order)
                return Response(
                    response_serializer.data, status=status.HTTP_201_CREATED
                )
            except Exception as e:
                logger.error(f"Order creation failed: {str(e)}", exc_info=True)
                return Response(
                    {"error": "Order creation failed", "detail": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            {"error": "Validation failed", "detail": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ShopkeeperOrderListView(generics.ListAPIView):
    """
    GET /api/shopkeeper/orders/
    List all orders for the authenticated shopkeeper
    """

    permission_classes = [permissions.IsAuthenticated, IsShopkeeper]
    serializer_class = OrderListSerializer

    def get_queryset(self):
        return (
            Order.objects.filter(shopkeeper=self.request.user)
            .select_related("warehouse", "shopkeeper")
            .order_by("-created_at")
        )


class ShopkeeperOrderDetailView(generics.RetrieveAPIView):
    """
    GET /api/shopkeeper/orders/{id}/
    Get details of a specific order
    """

    permission_classes = [permissions.IsAuthenticated, IsShopkeeper]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return (
            Order.objects.filter(shopkeeper=self.request.user)
            .select_related("shopkeeper", "warehouse", "delivery", "delivery__rider")
            .prefetch_related(
                Prefetch(
                    "order_items", queryset=OrderItem.objects.select_related("item")
                )
            )
        )


class WarehouseOrderListView(generics.ListAPIView):
    """
    GET /api/warehouse/orders/
    List all orders for the warehouse admin's warehouses
    """

    permission_classes = [permissions.IsAuthenticated, IsWarehouseAdmin]
    serializer_class = OrderListSerializer

    def get_queryset(self):
        # Get all warehouses managed by this admin
        warehouse_ids = self.request.user.warehouses.values_list("id", flat=True)

        # Filter by status if provided
        queryset = (
            Order.objects.filter(warehouse_id__in=warehouse_ids)
            .select_related("warehouse", "shopkeeper")
            .order_by("-created_at")
        )

        # Optional status filter
        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset


class WarehouseOrderDetailView(generics.RetrieveAPIView):
    """
    GET /api/warehouse/orders/{id}/
    Get details of a specific order for warehouse admin
    """

    permission_classes = [permissions.IsAuthenticated, IsWarehouseAdmin]
    serializer_class = OrderSerializer

    def get_queryset(self):
        warehouse_ids = self.request.user.warehouses.values_list("id", flat=True)

        return (
            Order.objects.filter(warehouse_id__in=warehouse_ids)
            .select_related("shopkeeper", "warehouse", "delivery", "delivery__rider")
            .prefetch_related(
                Prefetch(
                    "order_items", queryset=OrderItem.objects.select_related("item")
                )
            )
        )


class WarehousePendingOrdersView(generics.ListAPIView):
    """
    GET /api/warehouse/orders/pending/
    List all pending orders for warehouse admin's warehouses
    """

    permission_classes = [permissions.IsAuthenticated, IsWarehouseAdmin]
    serializer_class = OrderListSerializer

    def get_queryset(self):
        warehouse_ids = self.request.user.warehouses.values_list("id", flat=True)

        return (
            Order.objects.filter(warehouse_id__in=warehouse_ids, status="pending")
            .select_related("warehouse", "shopkeeper")
            .order_by("created_at")
        )  # Oldest first for pending


class OrderAcceptView(APIView):
    """
    POST /api/warehouse/orders/{id}/accept/
    Accept a pending order with state validation
    """

    permission_classes = [permissions.IsAuthenticated, IsWarehouseAdmin]

    def post(self, request, pk):
        # Validate ID
        is_valid, error_msg = IDValidator.validate_id(pk)
        if not is_valid:
            return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)

        try:
            warehouse_ids = request.user.warehouses.values_list("id", flat=True)

            order = Order.objects.select_related("warehouse", "shopkeeper").get(
                id=pk, warehouse_id__in=warehouse_ids
            )

            # Validate state transition
            can_transition, error_msg = OrderStateManager.validate_transition(
                order.status, "accepted", request.user.role
            )

            if not can_transition:
                logger.warning(
                    f"Invalid state transition attempt",
                    extra={
                        "order_id": order.id,
                        "user_id": request.user.id,
                        "from_state": order.status,
                        "to_state": "accepted",
                        "error": error_msg,
                    },
                )
                return Response(
                    {"error": error_msg}, status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                order.status = "accepted"
                order.save(update_fields=["status", "updated_at"])

                # Log state transition
                OrderStateManager.log_transition(
                    order.id, request.user.id, "pending", "accepted"
                )

            # Fetch updated order with full details
            order = (
                Order.objects.select_related("shopkeeper", "warehouse")
                .prefetch_related(
                    Prefetch(
                        "order_items", queryset=OrderItem.objects.select_related("item")
                    )
                )
                .get(id=order.id)
            )

            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )


class OrderRejectView(APIView):
    """
    POST /api/warehouse/orders/{id}/reject/
    Reject a pending order with a reason and state validation
    """

    permission_classes = [permissions.IsAuthenticated, IsWarehouseAdmin]

    def post(self, request, pk):
        # Validate ID
        is_valid, error_msg = IDValidator.validate_id(pk)
        if not is_valid:
            return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)

        try:
            warehouse_ids = request.user.warehouses.values_list("id", flat=True)

            order = Order.objects.select_related("warehouse", "shopkeeper").get(
                id=pk, warehouse_id__in=warehouse_ids
            )

            # Validate state transition
            can_transition, error_msg = OrderStateManager.validate_transition(
                order.status, "rejected", request.user.role
            )

            if not can_transition:
                return Response(
                    {"error": error_msg}, status=status.HTTP_400_BAD_REQUEST
                )

            rejection_reason = request.data.get("rejection_reason", "").strip()
            if not rejection_reason:
                return Response(
                    {"error": "Rejection reason is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate and sanitize rejection reason
            is_valid, error_msg = StringValidator.validate_length(
                rejection_reason, 10, 500, "Rejection reason"
            )
            if not is_valid:
                return Response(
                    {"error": error_msg}, status=status.HTTP_400_BAD_REQUEST
                )

            rejection_reason = StringValidator.sanitize_string(rejection_reason)

            with transaction.atomic():
                order.status = "rejected"
                order.rejection_reason = rejection_reason
                order.save(update_fields=["status", "rejection_reason", "updated_at"])

                # Log state transition
                OrderStateManager.log_transition(
                    order.id, request.user.id, "pending", "rejected", rejection_reason
                )

            # Fetch updated order with full details
            order = (
                Order.objects.select_related("shopkeeper", "warehouse")
                .prefetch_related(
                    Prefetch(
                        "order_items", queryset=OrderItem.objects.select_related("item")
                    )
                )
                .get(id=order.id)
            )

            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )


class OrderAssignmentView(APIView):
    """
    POST /api/warehouse/orders/assign/
    Assign a rider to an accepted order
    """

    permission_classes = [permissions.IsAuthenticated, IsWarehouseAdmin]

    def post(self, request):
        serializer = OrderAssignmentSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            order = serializer.validated_data["_order"]
            rider = serializer.validated_data["_rider"]

            with transaction.atomic():
                # Update order status to assigned
                order.status = "assigned"
                order.save(update_fields=["status", "updated_at"])

                # Create delivery record
                Delivery.objects.create(order=order, rider=rider, status="assigned")

            # Fetch updated order with full details including delivery
            order = (
                Order.objects.select_related(
                    "shopkeeper", "warehouse", "delivery", "delivery__rider"
                )
                .prefetch_related(
                    Prefetch(
                        "order_items", queryset=OrderItem.objects.select_related("item")
                    )
                )
                .get(id=order.id)
            )

            response_serializer = OrderSerializer(order)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        return Response(
            {"error": "Validation failed", "detail": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
