# analytics/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
import logging

from .models import AnalyticsSummary
from .serializers import (
    AnalyticsSummarySerializer,
    SystemAnalyticsSerializer,
    WarehouseAnalyticsSerializer,
    RiderAnalyticsSerializer,
)
from .tasks import (
    compute_system_analytics,
    compute_warehouse_analytics,
    compute_rider_analytics,
)
from core.permissions import IsSuperAdmin, IsWarehouseAdmin, IsRider

logger = logging.getLogger(__name__)


class AnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for analytics data.
    Provides read-only access to pre-computed analytics summaries.
    """
    queryset = AnalyticsSummary.objects.all()
    serializer_class = AnalyticsSummarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter analytics based on user role."""
        user = self.request.user
        queryset = super().get_queryset()

        # Admin can see all analytics
        if user.role == 'ADMIN' or user.is_superuser:
            return queryset

        # Warehouse managers can only see their warehouse analytics
        if user.role == 'WAREHOUSE_MANAGER':
            return queryset.filter(
                ref_type='warehouse',
                ref_id=user.warehouse_id
            )

        # Riders can only see their own analytics
        if user.role == 'RIDER':
            return queryset.filter(
                ref_type='rider',
                ref_id=user.rider_profile.id if hasattr(user, 'rider_profile') else None
            )

        # Shopkeepers can see their own analytics
        if user.role == 'SHOPKEEPER':
            return queryset.filter(
                ref_type='shopkeeper',
                ref_id=user.shopkeeper_profile.id if hasattr(user, 'shopkeeper_profile') else None
            )

        return queryset.none()

    @action(detail=False, methods=['get'], permission_classes=[IsSuperAdmin])
    def system(self, request):
        """
        Get system-wide analytics.
        Query params:
        - date: Date for analytics (default: yesterday)
        - days: Number of days to fetch (default: 7)
        """
        date_str = request.query_params.get('date')
        days = int(request.query_params.get('days', 7))

        if date_str:
            from datetime import datetime
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            target_date = (timezone.now() - timedelta(days=1)).date()

        # Try to get from cache first
        cache_key = f'system_analytics_{target_date}_{days}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)

        # Fetch from database
        summaries = AnalyticsSummary.objects.filter(
            ref_type='system',
            date__gte=target_date - timedelta(days=days-1),
            date__lte=target_date
        ).order_by('-date')

        if not summaries.exists():
            # Trigger computation
            compute_system_analytics.delay(target_date.isoformat())
            return Response(
                {'message': 'Analytics are being computed. Please try again in a moment.'},
                status=status.HTTP_202_ACCEPTED
            )

        data = [
            {
                'date': s.date,
                **s.metrics
            }
            for s in summaries
        ]

        # Cache for 1 hour
        cache.set(cache_key, data, 3600)
        
        return Response(data)

    @action(detail=False, methods=['get'], permission_classes=[IsSuperAdmin | IsWarehouseAdmin])
    def warehouse(self, request):
        """
        Get warehouse analytics.
        Query params:
        - warehouse_id: Warehouse ID (required for admin, auto-filled for warehouse managers)
        - date: Date for analytics (default: yesterday)
        - days: Number of days to fetch (default: 7)
        """
        user = request.user
        warehouse_id = request.query_params.get('warehouse_id')

        # Warehouse managers can only see their own warehouse
        if user.role == 'WAREHOUSE_MANAGER':
            warehouse_id = user.warehouse_id
        elif not warehouse_id:
            return Response(
                {'error': 'warehouse_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        date_str = request.query_params.get('date')
        days = int(request.query_params.get('days', 7))

        if date_str:
            from datetime import datetime
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            target_date = (timezone.now() - timedelta(days=1)).date()

        # Try to get from cache first
        cache_key = f'warehouse_analytics_{warehouse_id}_{target_date}_{days}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)

        # Fetch from database
        summaries = AnalyticsSummary.objects.filter(
            ref_type='warehouse',
            ref_id=warehouse_id,
            date__gte=target_date - timedelta(days=days-1),
            date__lte=target_date
        ).order_by('-date')

        if not summaries.exists():
            # Trigger computation
            compute_warehouse_analytics.delay(int(warehouse_id), target_date.isoformat())
            return Response(
                {'message': 'Analytics are being computed. Please try again in a moment.'},
                status=status.HTTP_202_ACCEPTED
            )

        data = [
            {
                'date': s.date,
                'warehouse_id': s.ref_id,
                **s.metrics
            }
            for s in summaries
        ]

        # Cache for 1 hour
        cache.set(cache_key, data, 3600)
        
        return Response(data)

    @action(detail=False, methods=['get'], permission_classes=[IsSuperAdmin | IsRider])
    def rider(self, request):
        """
        Get rider analytics.
        Query params:
        - rider_id: Rider ID (required for admin, auto-filled for riders)
        - date: Date for analytics (default: yesterday)
        - days: Number of days to fetch (default: 7)
        """
        user = request.user
        rider_id = request.query_params.get('rider_id')

        # Riders can only see their own analytics
        if user.role == 'RIDER':
            rider_id = user.rider_profile.id if hasattr(user, 'rider_profile') else None
            if not rider_id:
                return Response(
                    {'error': 'Rider profile not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif not rider_id:
            return Response(
                {'error': 'rider_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        date_str = request.query_params.get('date')
        days = int(request.query_params.get('days', 7))

        if date_str:
            from datetime import datetime
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            target_date = (timezone.now() - timedelta(days=1)).date()

        # Try to get from cache first
        cache_key = f'rider_analytics_{rider_id}_{target_date}_{days}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)

        # Fetch from database
        summaries = AnalyticsSummary.objects.filter(
            ref_type='rider',
            ref_id=rider_id,
            date__gte=target_date - timedelta(days=days-1),
            date__lte=target_date
        ).order_by('-date')

        if not summaries.exists():
            # Trigger computation
            compute_rider_analytics.delay(int(rider_id), target_date.isoformat())
            return Response(
                {'message': 'Analytics are being computed. Please try again in a moment.'},
                status=status.HTTP_202_ACCEPTED
            )

        data = [
            {
                'date': s.date,
                'rider_id': s.ref_id,
                **s.metrics
            }
            for s in summaries
        ]

        # Cache for 1 hour
        cache.set(cache_key, data, 3600)
        
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[IsSuperAdmin])
    def refresh(self, request):
        """
        Manually trigger analytics computation.
        Body params:
        - type: 'system', 'warehouse', or 'rider'
        - id: Entity ID (required for warehouse and rider)
        - date: Date to compute (default: yesterday)
        """
        analytics_type = request.data.get('type', 'system')
        entity_id = request.data.get('id')
        date_str = request.data.get('date')

        if date_str:
            from datetime import datetime
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            target_date = (timezone.now() - timedelta(days=1)).date()

        if analytics_type == 'system':
            compute_system_analytics.delay(target_date.isoformat())
        elif analytics_type == 'warehouse':
            if not entity_id:
                return Response(
                    {'error': 'warehouse id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            compute_warehouse_analytics.delay(int(entity_id), target_date.isoformat())
        elif analytics_type == 'rider':
            if not entity_id:
                return Response(
                    {'error': 'rider id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            compute_rider_analytics.delay(int(entity_id), target_date.isoformat())
        else:
            return Response(
                {'error': 'Invalid analytics type'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {'message': f'{analytics_type.capitalize()} analytics computation triggered'},
            status=status.HTTP_202_ACCEPTED
        )
