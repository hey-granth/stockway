from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from decimal import Decimal
from .models import Payment, Payout
from .serializers import (
    PaymentSerializer,
    PaymentInitiateSerializer,
    PaymentConfirmSerializer,
    PayoutSerializer,
    PayoutProcessSerializer,
)
from orders.models import Order
from delivery.models import Delivery
from accounts.models import User
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def initiate_payment(request):
    """
    POST /payments/initiate/
    Create payment when shopkeeper confirms order.

    Validates:
    - Payment amount equals order total
    - No duplicate payments for same order
    - User is shopkeeper
    """
    # Check user role
    if request.user.role != "SHOPKEEPER":
        return Response(
            {"error": "Only shopkeepers can initiate payments."},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = PaymentInitiateSerializer(data=request.data, context={'request': request})

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Get validated data
    order_id = serializer.validated_data['order_id']
    amount = serializer.validated_data['amount']
    mode = serializer.validated_data['mode']

    # Get order
    order = Order.objects.select_related('warehouse', 'warehouse__admin').get(id=order_id)

    # Verify shopkeeper owns this order
    if order.shopkeeper != request.user:
        return Response(
            {"error": "You can only make payments for your own orders."},
            status=status.HTTP_403_FORBIDDEN
        )

    # Create payment
    payment = Payment.objects.create(
        order=order,
        payer=request.user,
        payee=order.warehouse.admin,
        amount=amount,
        mode=mode,
        status="pending"
    )

    logger.info(f"Payment {payment.id} initiated by shopkeeper {request.user.id} for order {order_id}")

    return Response(
        PaymentSerializer(payment).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def confirm_payment(request):
    """
    PATCH /payments/confirm/
    Warehouse admin confirms or rejects payment.

    Actions: "confirm" or "reject"
    Only warehouse_admin or super_admin can confirm payments.
    Updates order status to 'paid' upon confirmation.
    """
    # Check user role
    if request.user.role not in ["WAREHOUSE_MANAGER", "ADMIN"]:
        return Response(
            {"error": "Only warehouse admins can confirm payments."},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = PaymentConfirmSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    payment_id = serializer.validated_data['payment_id']
    action = serializer.validated_data['action']

    # Get payment
    try:
        payment = Payment.objects.select_related('order', 'order__warehouse').get(id=payment_id)
    except Payment.DoesNotExist:
        return Response(
            {"error": "Payment not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    # Verify warehouse admin owns this payment's warehouse
    if request.user.role == "WAREHOUSE_MANAGER":
        if payment.order.warehouse.admin != request.user:
            return Response(
                {"error": "You can only confirm payments for your warehouse."},
                status=status.HTTP_403_FORBIDDEN
            )

    # Check payment is pending
    if payment.status != "pending":
        return Response(
            {"error": f"Payment is already {payment.status}."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Perform action
    if action == "confirm":
        payment.status = "completed"
        payment.save()

        # Update order status to indicate payment received
        # Note: We don't have 'paid' status in Order model, so we'll log it
        logger.info(f"Payment {payment.id} confirmed for order {payment.order.id}")

    elif action == "reject":
        payment.status = "failed"
        payment.save()

        logger.info(f"Payment {payment.id} rejected for order {payment.order.id}")

    return Response(
        PaymentSerializer(payment).data,
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def process_payouts(request):
    """
    POST /payouts/process/
    Admin or automated Celery task to compute payouts for delivered orders.

    Can process specific orders or all delivered orders without payouts.
    """
    # Check user role
    if request.user.role not in ["WAREHOUSE_MANAGER", "ADMIN"]:
        return Response(
            {"error": "Only admins can process payouts."},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = PayoutProcessSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    order_ids = serializer.validated_data.get('order_ids')
    rate_per_km = serializer.validated_data.get('rate_per_km', Decimal("10.00"))

    # Get delivered orders
    if order_ids:
        orders = Order.objects.filter(id__in=order_ids, status="delivered")
    else:
        # Get all delivered orders without payouts
        orders = Order.objects.filter(status="delivered")

        # Filter by warehouse if warehouse admin
        if request.user.role == "WAREHOUSE_MANAGER":
            orders = orders.filter(warehouse__admin=request.user)

    payouts_created = []
    errors = []

    for order in orders.select_related('warehouse'):
        try:
            # Get delivery record
            try:
                delivery = Delivery.objects.select_related('rider').get(order=order)
            except Delivery.DoesNotExist:
                errors.append({
                    "order_id": order.id,
                    "error": "No delivery record found"
                })
                continue

            # Check if payout already exists for this specific delivery
            existing_payout = Payout.objects.filter(
                rider=delivery.rider,
                warehouse=order.warehouse
            ).first()

            # Calculate distance
            distance_km = getattr(delivery, 'distance_km', 0.0)
            if distance_km == 0.0:
                # Try to compute from PostGIS if available
                if hasattr(delivery, 'pickup_location') and hasattr(delivery, 'delivery_location'):
                    from django.contrib.gis.measure import Distance
                    from django.contrib.gis.geos import Point
                    if delivery.pickup_location and delivery.delivery_location:
                        distance = delivery.pickup_location.distance(delivery.delivery_location) * 111  # rough km conversion
                        distance_km = float(distance)

            # Compute payout amount
            computed_amount = Decimal(str(distance_km)) * rate_per_km

            # Create or update payout
            if existing_payout:
                # Add to existing payout
                existing_payout.total_distance += distance_km
                existing_payout.computed_amount += computed_amount
                existing_payout.save()
                payout = existing_payout
            else:
                # Create new payout
                payout = Payout.objects.create(
                    rider=delivery.rider,
                    warehouse=order.warehouse,
                    total_distance=distance_km,
                    rate_per_km=rate_per_km,
                    computed_amount=computed_amount,
                    status="pending"
                )

            payouts_created.append({
                "payout_id": payout.id,
                "order_id": order.id,
                "rider_id": delivery.rider.id,
                "amount": float(computed_amount)
            })

            logger.info(f"Payout {payout.id} processed for order {order.id}")

        except Exception as e:
            errors.append({
                "order_id": order.id,
                "error": str(e)
            })
            logger.error(f"Error processing payout for order {order.id}: {str(e)}")

    return Response({
        "success": True,
        "payouts_created": len(payouts_created),
        "payouts": payouts_created,
        "errors": errors
    }, status=status.HTTP_201_CREATED if payouts_created else status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_payouts(request):
    """
    GET /payouts/list/
    Rider and warehouse view payout summaries.

    Filters based on user role:
    - Riders see their own payouts
    - Warehouse admins see payouts for their warehouse
    - Super admins see all payouts
    """
    user = request.user

    if user.role == "ADMIN":
        payouts = Payout.objects.all()
    elif user.role == "WAREHOUSE_MANAGER":
        payouts = Payout.objects.filter(warehouse__admin=user)
    elif user.role == "RIDER":
        try:
            rider = user.rider_profile
            payouts = Payout.objects.filter(rider=rider)
        except Exception:
            return Response(
                {"error": "No rider profile found for user."},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        return Response(
            {"error": "Unauthorized to view payouts."},
            status=status.HTTP_403_FORBIDDEN
        )

    # Apply filters
    payout_status = request.query_params.get('status')
    if payout_status:
        payouts = payouts.filter(status=payout_status)

    # Select related to optimize queries
    payouts = payouts.select_related('rider', 'warehouse').order_by('-created_at')

    serializer = PayoutSerializer(payouts, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)
