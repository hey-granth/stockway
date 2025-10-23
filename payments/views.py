from decimal import Decimal
from django.db.models import QuerySet
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Payment
from .serializers import (
    PaymentSerializer,
    CreateShopkeeperPaymentSerializer,
    CreateRiderPayoutSerializer,
    UpdatePaymentStatusSerializer,
)
from accounts.models import User


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling payment operations.

    Endpoints:
    - GET /payments/ - List all payments (filtered by user role)
    - POST /payments/shopkeeper-payment/ - Shopkeeper pays warehouse for an order
    - POST /payments/rider-payout/ - Warehouse admin creates payout for rider
    - PATCH /payments/{id}/complete/ - Mark payment as completed (mock payment)
    - PATCH /payments/{id}/fail/ - Mark payment as failed
    """

    queryset = Payment.objects.select_related(
        "order", "warehouse", "payer", "payee", "rider"
    ).all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields = ["status", "payment_type", "warehouse", "rider", "order"]
    ordering_fields = ["created_at", "amount", "status"]
    search_fields = ["transaction_id", "notes"]

    def get_queryset(self) -> QuerySet[Payment, Payment]:
        """Filter payments based on user role."""
        user = self.request.user

        if user.role == User.Role.SUPER_ADMIN:
            # Super admin sees all payments
            return self.queryset
        elif user.role == User.Role.WAREHOUSE_ADMIN:
            # Warehouse admin sees payments related to their warehouses
            return self.queryset.filter(warehouse__admin=user)
        elif user.role == User.Role.SHOPKEEPER:
            # Shopkeeper sees their own payments
            return self.queryset.filter(payer=user)
        elif user.role == User.Role.RIDER:
            # Rider sees their payouts
            return self.queryset.filter(rider=user)

        return Payment.objects.none()

    @action(detail=False, methods=["post"], url_path="shopkeeper-payment")
    @transaction.atomic
    def shopkeeper_payment(self, request) -> Response:
        """
        Create a payment from shopkeeper to warehouse for an order.
        Shopkeepers only.
        """
        if request.user.role != User.Role.SHOPKEEPER:
            return Response(
                {"error": "Only shopkeepers can make payments to warehouses."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CreateShopkeeperPaymentSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            payment = serializer.save()
            return Response(
                PaymentSerializer(payment).data, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="rider-payout")
    @transaction.atomic
    def rider_payout(self, request) -> Response:
        """
        Create a payout from warehouse to rider for a delivered order.
        Warehouse admins and super admins only.
        """
        if request.user.role not in [User.Role.WAREHOUSE_ADMIN, User.Role.SUPER_ADMIN]:
            return Response(
                {"error": "Only warehouse admins can create rider payouts."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CreateRiderPayoutSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            payment = serializer.save()
            return Response(
                PaymentSerializer(payment).data, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"], url_path="complete")
    @transaction.atomic
    def complete_payment(self, request, pk=None) -> Response:
        """
        Mark a payment as completed (mock payment completion).
        Warehouse admins for shopkeeper payments, super admins for all.
        """
        payment = self.get_object()

        # Permission check
        if request.user.role == User.Role.WAREHOUSE_ADMIN:
            if payment.warehouse.admin != request.user:
                return Response(
                    {"error": "You can only complete payments for your warehouse."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        elif request.user.role != User.Role.SUPER_ADMIN:
            return Response(
                {"error": "Insufficient permissions."}, status=status.HTTP_403_FORBIDDEN
            )

        if payment.status == "completed":
            return Response(
                {"error": "Payment is already completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment.status = "completed"
        payment.completed_at = timezone.now()
        payment.save()

        return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["patch"], url_path="fail")
    @transaction.atomic
    def fail_payment(self, request, pk=None) -> Response:
        """
        Mark a payment as failed.
        Warehouse admins for their payments, super admins for all.
        """
        payment = self.get_object()

        # Permission check
        if request.user.role == User.Role.WAREHOUSE_ADMIN:
            if payment.warehouse.admin != request.user:
                return Response(
                    {"error": "You can only modify payments for your warehouse."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        elif request.user.role != User.Role.SUPER_ADMIN:
            return Response(
                {"error": "Insufficient permissions."}, status=status.HTTP_403_FORBIDDEN
            )

        if payment.status == "completed":
            return Response(
                {"error": "Cannot fail a completed payment."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UpdatePaymentStatusSerializer(
            payment,
            data={"status": "failed", "notes": request.data.get("notes", "")},
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], url_path="statistics")
    def statistics(self, request) -> Response:
        """
        Get payment statistics for the requesting user.
        """
        user = request.user
        queryset = self.get_queryset()

        stats: dict[str, int | Decimal] = {
            "total_payments": queryset.count(),
            "pending": queryset.filter(status="pending").count(),
            "completed": queryset.filter(status="completed").count(),
            "failed": queryset.filter(status="failed").count(),
            "total_amount_pending": sum(
                p.amount for p in queryset.filter(status="pending")
            ),
            "total_amount_completed": sum(
                p.amount for p in queryset.filter(status="completed")
            ),
        }

        if user.role == User.Role.WAREHOUSE_ADMIN:
            stats["shopkeeper_payments"] = queryset.filter(
                payment_type="shopkeeper_to_warehouse"
            ).count()
            stats["rider_payouts"] = queryset.filter(
                payment_type="warehouse_to_rider"
            ).count()

        return Response(stats, status=status.HTTP_200_OK)
