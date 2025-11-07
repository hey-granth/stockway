# riders/views.py
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
from django.db.models import Q, F
from django.utils import timezone
from django.http import HttpResponse
from decimal import Decimal
from datetime import datetime, timedelta
import logging
import csv
import io

from .models import Rider, RiderNotification
from .serializers import (
    RiderSerializer,
    RiderRegistrationSerializer,
    RiderProfileSerializer,
    RiderLocationUpdateSerializer,
    RiderListSerializer,
    RiderEarningsSerializer,
    RiderHistorySerializer,
    RiderPerformanceSerializer,
    RiderNotificationSerializer,
    RiderAvailabilitySerializer,
    ActiveRiderSerializer,
    WarehouseRiderMetricsSerializer,
    RiderManagementSerializer,
)
from .services import (
    RedisService,
    LocationTrackingService,
    EarningsService,
    PerformanceMetricsService,
    NotificationService,
)
from orders.models import Order
from orders.serializers import OrderListSerializer
from warehouses.models import Warehouse, RiderPayout
from core.permissions import IsRider, IsWarehouseAdminOrSuperAdmin
from core.throttling import LocationUpdateThrottle

logger = logging.getLogger(__name__)


class StandardResultsPagination(PageNumberPagination):
    """Standard pagination for rider endpoints"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class RiderRegistrationView(APIView):
    """
    POST /api/rider/register/
    Register a new rider (warehouse_admin or super_admin only)
    """

    permission_classes = [permissions.IsAuthenticated, IsWarehouseAdminOrSuperAdmin]

    def post(self, request):
        serializer = RiderRegistrationSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            try:
                rider = serializer.save()
                response_serializer = RiderSerializer(rider)
                return Response(
                    response_serializer.data, status=status.HTTP_201_CREATED
                )
            except Exception as e:
                logger.error(f"Rider registration failed: {str(e)}", exc_info=True)
                return Response(
                    {"error": "Rider registration failed", "detail": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            {"error": "Validation failed", "detail": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class RiderProfileView(APIView):
    """
    GET /api/rider/profile/
    Get rider profile details

    PUT /api/rider/profile/
    Update rider profile (limited fields)
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def get(self, request):
        try:
            rider = Rider.objects.select_related("user", "warehouse").get(
                user=request.user
            )
            serializer = RiderProfileSerializer(rider)
            return Response(serializer.data)
        except Rider.DoesNotExist:
            return Response(
                {"error": "Rider profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def put(self, request):
        try:
            rider = Rider.objects.select_related("user", "warehouse").get(
                user=request.user
            )
        except Rider.DoesNotExist:
            return Response(
                {"error": "Rider profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Only allow updating specific fields
        allowed_fields = ["status"]
        update_data = {k: v for k, v in request.data.items() if k in allowed_fields}

        serializer = RiderProfileSerializer(rider, data=update_data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(
            {"error": "Validation failed", "detail": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class RiderOrdersView(ListAPIView):
    """
    GET /api/rider/orders/
    Get assigned orders (status != delivered)
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]
    serializer_class = OrderListSerializer

    def get_queryset(self):
        # Get orders assigned to this rider that are not delivered
        return (
            Order.objects.filter(
                delivery__rider=self.request.user,
            )
            .exclude(status="delivered")
            .select_related("shopkeeper", "warehouse", "delivery")
            .order_by("-created_at")
        )


class RiderOrderUpdateView(APIView):
    """
    PATCH /api/rider/orders/update/
    Update order status transitions (assigned → in_transit → delivered)
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def patch(self, request):
        order_id = request.data.get("order_id")
        new_status = request.data.get("status")

        if not order_id or not new_status:
            return Response(
                {"error": "order_id and status are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate status
        valid_statuses = ["assigned", "in_transit", "delivered"]
        if new_status not in valid_statuses:
            return Response(
                {
                    "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Get order assigned to this rider
            order = Order.objects.select_related(
                "delivery", "warehouse", "shopkeeper"
            ).get(id=order_id, delivery__rider=request.user)

        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found or not assigned to you"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Validate state transitions
        current_status = order.status
        valid_transitions = {
            "assigned": ["in_transit"],
            "in_transit": ["delivered"],
            "delivered": [],
        }

        if new_status not in valid_transitions.get(current_status, []):
            return Response(
                {
                    "error": f"Invalid transition from {current_status} to {new_status}",
                    "detail": f"Valid transitions from {current_status}: {', '.join(valid_transitions.get(current_status, []))}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                # Update order status
                order.status = new_status
                order.save()

                # Update delivery status
                if order.delivery:
                    order.delivery.status = new_status
                    order.delivery.save()

                # Handle delivery completion
                if new_status == "delivered":
                    self._handle_delivery_completion(order)

                logger.info(
                    f"Order {order.id} status updated to {new_status} by rider {request.user.id}"
                )

                response_data = {
                    "order_id": order.id,
                    "status": order.status,
                    "message": f"Order status updated to {new_status}",
                }

                # Add payout info if delivered
                if new_status == "delivered":
                    rider = Rider.objects.get(user=request.user)
                    response_data["payout_summary"] = {
                        "rider_id": rider.id,
                        "total_earnings": str(rider.total_earnings),
                        "delivery_payout": str(order.delivery.delivery_fee),
                    }

                return Response(response_data)

        except Exception as e:
            logger.error(f"Order status update failed: {str(e)}", exc_info=True)
            return Response(
                {"error": "Order status update failed", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _handle_delivery_completion(self, order):
        """Handle delivery completion logic"""
        try:
            rider = Rider.objects.get(user=order.delivery.rider)

            # Calculate payout
            base_rate = Decimal("50.00")  # Base delivery fee
            rate_per_km = Decimal("10.00")  # Rate per km

            # Calculate distance if locations are available
            distance_km = Decimal("0.00")
            if rider.current_location and order.warehouse.location:
                from django.contrib.gis.db.models.functions import Distance

                # Calculate distance in meters and convert to km
                distance_meters = rider.current_location.distance(
                    order.warehouse.location
                )
                distance_km = Decimal(str(distance_meters / 1000)).quantize(
                    Decimal("0.01")
                )

            payout = base_rate + (distance_km * rate_per_km)

            # Update rider status and earnings
            rider.status = "available"
            rider.total_earnings += payout
            rider.save()

            # Update delivery fee
            order.delivery.delivery_fee = payout
            order.delivery.save()

            # Create payout record using RiderPayout
            RiderPayout.objects.create(
                warehouse=order.warehouse,
                rider=rider,
                order=order,
                base_rate=base_rate,
                distance_km=distance_km,
                distance_rate=rate_per_km,
                status="pending"
            )

            logger.info(
                f"Delivery completed. Rider {rider.id} earned {payout} for order {order.id}"
            )

        except Rider.DoesNotExist:
            logger.error(f"Rider profile not found for user {order.delivery.rider.id}")
        except Exception as e:
            logger.error(f"Error handling delivery completion: {str(e)}", exc_info=True)
            raise


class RiderLocationUpdateView(APIView):
    """
    PATCH /api/rider/location/update/
    Update rider's current location
    """

    permission_classes = [permissions.IsAuthenticated, IsRider]

    def patch(self, request):
        serializer = RiderLocationUpdateSerializer(data=request.data)

        if serializer.is_valid():
            try:
                rider = Rider.objects.get(user=request.user)

                latitude = serializer.validated_data["latitude"]
                longitude = serializer.validated_data["longitude"]

                rider.set_coordinates(latitude, longitude)
                rider.save()

                return Response(
                    {
                        "message": "Location updated successfully",
                        "latitude": latitude,
                        "longitude": longitude,
                    }
                )

            except Rider.DoesNotExist:
                return Response(
                    {"error": "Rider profile not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            except Exception as e:
                logger.error(f"Location update failed: {str(e)}", exc_info=True)
                return Response(
                    {"error": "Location update failed", "detail": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(
            {"error": "Validation failed", "detail": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class WarehouseRidersListView(ListAPIView):
    """
    GET /api/warehouse/riders/
    List all riders for warehouse admin's warehouses
    """

    permission_classes = [permissions.IsAuthenticated, IsWarehouseAdminOrSuperAdmin]
    serializer_class = RiderListSerializer

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser or user.role == "ADMIN":
            # Super admin can see all riders
            queryset = Rider.objects.all()
        else:
            # Warehouse admin sees only their warehouse riders
            warehouse_ids = user.warehouses.values_list("id", flat=True)
            queryset = Rider.objects.filter(warehouse_id__in=warehouse_ids)

        # Optional status filter
        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset.select_related("user", "warehouse").order_by("-created_at")


class RiderDetailView(APIView):
    """
    GET /api/warehouse/riders/{id}/
    Get detailed rider information (warehouse admin or super admin)
    """

    permission_classes = [permissions.IsAuthenticated, IsWarehouseAdminOrSuperAdmin]

    def get(self, request, pk):
        try:
            rider = Rider.objects.select_related("user", "warehouse").get(id=pk)

            # Check permission for warehouse admin
            if (
                request.user.role == "WAREHOUSE_MANAGER"
                and rider.warehouse.admin != request.user
            ):
                return Response(
                    {"error": "You can only view riders in your warehouse"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            serializer = RiderSerializer(rider)
            return Response(serializer.data)

        except Rider.DoesNotExist:
            return Response(
                {"error": "Rider not found"}, status=status.HTTP_404_NOT_FOUND
            )


# ============ NEW ADVANCED FEATURES ============


class RiderEarningsView(APIView):
    """
    GET /api/rider/earnings/
    Get rider earnings summary with filtering by date range
    Query params: period (daily/weekly/monthly), start_date, end_date
    """
    permission_classes = [permissions.IsAuthenticated, IsRider]

    def get(self, request):
        try:
            rider = Rider.objects.get(user=request.user)
        except Rider.DoesNotExist:
            return Response(
                {"error": "Rider profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Parse date parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        period = request.query_params.get('period', 'daily')

        if start_date:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        # Get earnings summary
        summary = EarningsService.get_earnings_summary(rider, start_date, end_date)

        # Get period breakdown
        period_data = EarningsService.get_earnings_by_period(
            rider, period, start_date, end_date
        )

        return Response({
            'summary': summary,
            'period_breakdown': period_data
        })


class RiderHistoryView(ListAPIView):
    """
    GET /api/rider/history/
    Paginated delivery history for rider
    """
    permission_classes = [permissions.IsAuthenticated, IsRider]
    pagination_class = StandardResultsPagination

    def get(self, request):
        try:
            rider = Rider.objects.get(user=request.user)
        except Rider.DoesNotExist:
            return Response(
                {"error": "Rider profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get completed payouts with related data
        payouts = RiderPayout.objects.filter(
            rider=rider,
            status='completed'
        ).select_related(
            'order',
            'warehouse'
        ).order_by('-created_at')

        # Paginate
        paginator = self.pagination_class()
        paginated_payouts = paginator.paginate_queryset(payouts, request)

        # Format response
        history_data = []
        for payout in paginated_payouts:
            history_data.append({
                'order_id': payout.order.id,
                'warehouse_name': payout.warehouse.name,
                'warehouse_id': payout.warehouse.id,
                'distance_km': float(payout.distance_km),
                'payout_amount': float(payout.total_amount),
                'delivery_date': payout.created_at,
                'status': payout.status
            })

        return paginator.get_paginated_response(history_data)


class RiderLiveLocationView(APIView):
    """
    PATCH /api/rider/live-location/
    Update rider's live location with security checks and Redis caching
    Rate-limited to prevent spam
    """
    permission_classes = [permissions.IsAuthenticated, IsRider]
    throttle_classes = [LocationUpdateThrottle]

    def patch(self, request):
        serializer = RiderLocationUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "detail": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            rider = Rider.objects.get(user=request.user)

            # Check if rider is suspended
            if rider.is_suspended:
                return Response(
                    {"error": "Your account is suspended. Contact support."},
                    status=status.HTTP_403_FORBIDDEN
                )

            latitude = serializer.validated_data["latitude"]
            longitude = serializer.validated_data["longitude"]

            # Update location with tracking and security checks
            result = LocationTrackingService.update_location_with_tracking(
                rider, latitude, longitude
            )

            response_data = {
                "message": "Location updated successfully",
                "latitude": latitude,
                "longitude": longitude
            }

            # Warn if suspicious activity detected
            if result.get('is_suspicious'):
                response_data['warning'] = 'Suspicious movement detected'
                response_data['speed_kmh'] = result.get('speed_kmh')
                logger.warning(
                    f"Suspicious location update for rider {rider.id}: "
                    f"speed={result.get('speed_kmh')} km/h, "
                    f"distance={result.get('distance_km')} km"
                )

            return Response(response_data)

        except Rider.DoesNotExist:
            return Response(
                {"error": "Rider profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Live location update failed: {str(e)}", exc_info=True)
            return Response(
                {"error": "Location update failed", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RiderPerformanceView(APIView):
    """
    GET /api/rider/performance/
    Get rider performance metrics
    """
    permission_classes = [permissions.IsAuthenticated, IsRider]

    def get(self, request):
        try:
            rider = Rider.objects.get(user=request.user)
        except Rider.DoesNotExist:
            return Response(
                {"error": "Rider profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check cache first
        redis_service = RedisService()
        cached_metrics = redis_service.get_rider_metrics(rider.id)

        if cached_metrics:
            return Response(cached_metrics)

        # Calculate metrics
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        metrics = PerformanceMetricsService.calculate_performance_metrics(
            rider, start_date, end_date
        )

        monthly_aggregates = PerformanceMetricsService.get_monthly_aggregates(rider)
        metrics['monthly_aggregates'] = monthly_aggregates

        # Cache the results
        redis_service.cache_rider_metrics(rider.id, metrics)

        return Response(metrics)


class RiderAvailabilityUpdateView(APIView):
    """
    PATCH /api/rider/availability/update/
    Toggle rider availability status (available/off-duty)
    """
    permission_classes = [permissions.IsAuthenticated, IsRider]

    def patch(self, request):
        serializer = RiderAvailabilitySerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "detail": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            rider = Rider.objects.get(user=request.user)

            availability = serializer.validated_data['availability']
            rider.availability = availability

            # If going off-duty, also set status to inactive
            if availability == 'off-duty':
                rider.status = 'inactive'
            elif availability == 'available' and rider.status == 'inactive':
                rider.status = 'available'

            rider.save()

            return Response({
                'message': 'Availability updated successfully',
                'availability': rider.availability,
                'status': rider.status
            })

        except Rider.DoesNotExist:
            return Response(
                {"error": "Rider profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class RiderNotificationsView(ListAPIView):
    """
    GET /api/rider/notifications/
    Get rider notifications with read/unread filtering
    """
    permission_classes = [permissions.IsAuthenticated, IsRider]
    serializer_class = RiderNotificationSerializer
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        rider = Rider.objects.get(user=self.request.user)
        queryset = RiderNotification.objects.filter(rider=rider)

        # Filter by read/unread
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')

        return queryset.order_by('-created_at')


class RiderNotificationMarkReadView(APIView):
    """
    PATCH /api/rider/notifications/{id}/mark-read/
    Mark a notification as read
    """
    permission_classes = [permissions.IsAuthenticated, IsRider]

    def patch(self, request, pk):
        try:
            rider = Rider.objects.get(user=request.user)
            notification = RiderNotification.objects.get(id=pk, rider=rider)

            notification.is_read = True
            notification.save()

            return Response({
                'message': 'Notification marked as read',
                'notification_id': notification.id
            })

        except Rider.DoesNotExist:
            return Response(
                {"error": "Rider profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except RiderNotification.DoesNotExist:
            return Response(
                {"error": "Notification not found"},
                status=status.HTTP_404_NOT_FOUND
            )


# ============ WAREHOUSE ADMIN VIEWS ============


class WarehouseActiveRidersView(APIView):
    """
    GET /api/warehouse/riders/active/
    Get active riders with live locations from Redis
    """
    permission_classes = [permissions.IsAuthenticated, IsWarehouseAdminOrSuperAdmin]

    def get(self, request):
        user = request.user

        # Get warehouse IDs for this admin
        if user.is_superuser or user.role == "ADMIN":
            warehouse_ids = Warehouse.objects.values_list('id', flat=True)
        else:
            warehouse_ids = user.warehouses.values_list('id', flat=True)

        # Get riders from warehouse(s)
        riders = Rider.objects.filter(
            warehouse_id__in=warehouse_ids,
            availability='available'
        ).select_related('user', 'warehouse')

        # Get live locations from Redis
        redis_service = RedisService()
        active_riders_data = []

        for rider in riders:
            location_data = redis_service.get_rider_location(rider.id)

            if location_data:
                active_riders_data.append({
                    'rider_id': rider.id,
                    'name': rider.user.full_name or rider.user.email,
                    'email': rider.user.email,
                    'latitude': location_data['latitude'],
                    'longitude': location_data['longitude'],
                    'last_update': location_data['timestamp'],
                    'status': rider.status
                })

        return Response({
            'active_riders': active_riders_data,
            'total_count': len(active_riders_data)
        })


class WarehouseRiderMetricsView(APIView):
    """
    GET /api/warehouse/riders/metrics/
    Get performance metrics for all riders in warehouse
    """
    permission_classes = [permissions.IsAuthenticated, IsWarehouseAdminOrSuperAdmin]

    def get(self, request):
        user = request.user

        # Get warehouse IDs
        if user.is_superuser or user.role == "ADMIN":
            warehouse_ids = Warehouse.objects.values_list('id', flat=True)
        else:
            warehouse_ids = user.warehouses.values_list('id', flat=True)

        # Get riders
        riders = Rider.objects.filter(
            warehouse_id__in=warehouse_ids
        ).select_related('user')

        metrics_data = []
        for rider in riders:
            # Calculate metrics for each rider
            performance = PerformanceMetricsService.calculate_performance_metrics(rider)

            metrics_data.append({
                'rider_id': rider.id,
                'rider_name': rider.user.full_name or rider.user.email,
                'rider_email': rider.user.email,
                'total_earnings': float(rider.total_earnings),
                'completed_orders': performance['successful_deliveries'],
                'total_distance_km': performance['total_distance_km'],
                'success_rate': performance['success_rate'],
                'average_delivery_time_minutes': performance['average_delivery_time_minutes'],
                'status': rider.status,
                'availability': rider.availability
            })

        return Response({
            'riders': metrics_data,
            'total_riders': len(metrics_data)
        })


# ============ ADMIN CONTROL VIEWS ============


class AdminRiderManagementView(APIView):
    """
    POST /api/admin/riders/manage/
    Suspend, reactivate, or reassign riders
    """
    permission_classes = [permissions.IsAuthenticated, IsWarehouseAdminOrSuperAdmin]

    def post(self, request):
        serializer = RiderManagementSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "detail": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        action = serializer.validated_data['action']
        rider_id = serializer.validated_data['rider_id']
        reason = serializer.validated_data.get('reason', '')
        new_warehouse_id = serializer.validated_data.get('new_warehouse_id')

        try:
            rider = Rider.objects.select_related('user', 'warehouse').get(id=rider_id)

            # Check permissions for warehouse admin
            if request.user.role == 'WAREHOUSE_MANAGER':
                if rider.warehouse.admin != request.user:
                    return Response(
                        {"error": "You can only manage riders in your warehouse"},
                        status=status.HTTP_403_FORBIDDEN
                    )

            # Execute action
            if action == 'suspend':
                rider.is_suspended = True
                rider.suspension_reason = reason
                rider.status = 'inactive'
                rider.availability = 'off-duty'
                rider.save()

                # Send notification
                NotificationService.create_notification(
                    rider=rider,
                    notification_type='suspension',
                    title='Account Suspended',
                    message=f'Your account has been suspended. Reason: {reason}',
                    metadata={'reason': reason}
                )

                message = f'Rider {rider.id} suspended successfully'

            elif action == 'reactivate':
                rider.is_suspended = False
                rider.suspension_reason = None
                rider.status = 'available'
                rider.availability = 'available'
                rider.save()

                # Send notification
                NotificationService.create_notification(
                    rider=rider,
                    notification_type='general',
                    title='Account Reactivated',
                    message='Your account has been reactivated. You can now accept orders.',
                    metadata={}
                )

                message = f'Rider {rider.id} reactivated successfully'

            elif action == 'reassign':
                if not new_warehouse_id:
                    return Response(
                        {"error": "new_warehouse_id is required for reassignment"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                new_warehouse = Warehouse.objects.get(id=new_warehouse_id)
                old_warehouse = rider.warehouse

                rider.warehouse = new_warehouse
                rider.save()

                # Send notification
                NotificationService.create_notification(
                    rider=rider,
                    notification_type='general',
                    title='Warehouse Reassignment',
                    message=f'You have been reassigned from {old_warehouse.name} to {new_warehouse.name}',
                    metadata={
                        'old_warehouse_id': old_warehouse.id,
                        'new_warehouse_id': new_warehouse.id
                    }
                )

                message = f'Rider {rider.id} reassigned to warehouse {new_warehouse_id}'

            logger.info(f"Admin action: {action} on rider {rider.id} by {request.user.id}")

            return Response({
                'message': message,
                'rider_id': rider.id,
                'action': action
            })

        except Rider.DoesNotExist:
            return Response(
                {"error": "Rider not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Warehouse.DoesNotExist:
            return Response(
                {"error": "Warehouse not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Rider management action failed: {str(e)}", exc_info=True)
            return Response(
                {"error": "Action failed", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminRiderPayoutExportView(APIView):
    """
    GET /api/admin/riders/export/payouts/
    Export rider payouts and performance as CSV
    Query params: start_date, end_date, warehouse_id
    """
    permission_classes = [permissions.IsAuthenticated, IsWarehouseAdminOrSuperAdmin]

    def get(self, request):
        user = request.user

        # Get warehouse IDs
        if user.is_superuser or user.role == "ADMIN":
            warehouse_ids = Warehouse.objects.values_list('id', flat=True)
        else:
            warehouse_ids = user.warehouses.values_list('id', flat=True)

        # Parse filters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        warehouse_id = request.query_params.get('warehouse_id')

        # Query payouts
        payouts = RiderPayout.objects.filter(
            warehouse_id__in=warehouse_ids,
            status='completed'
        ).select_related('rider', 'rider__user', 'warehouse', 'order')

        if start_date:
            payouts = payouts.filter(created_at__gte=start_date)
        if end_date:
            payouts = payouts.filter(created_at__lte=end_date)
        if warehouse_id:
            payouts = payouts.filter(warehouse_id=warehouse_id)

        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Payout ID',
            'Rider ID',
            'Rider Name',
            'Rider Email',
            'Warehouse',
            'Order ID',
            'Distance (km)',
            'Base Rate',
            'Distance Rate',
            'Total Amount',
            'Date',
            'Status'
        ])

        # Write data
        for payout in payouts:
            writer.writerow([
                payout.id,
                payout.rider.id,
                payout.rider.user.full_name or payout.rider.user.email,
                payout.rider.user.email,
                payout.warehouse.name,
                payout.order.id,
                float(payout.distance_km),
                float(payout.base_rate),
                float(payout.distance_rate),
                float(payout.total_amount),
                payout.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                payout.status
            ])

        # Create response
        output.seek(0)
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="rider_payouts.csv"'

        return response


