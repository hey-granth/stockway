"""
Rider services for Redis caching, location tracking, and analytics
"""
import redis
import json
from decimal import Decimal
from datetime import datetime, timedelta
from django.contrib.gis.geos import Point
from django.db.models import Count, Sum, Q
from django.utils import timezone
from core.config import Config
import logging

logger = logging.getLogger(__name__)


class RedisService:
    """Redis service for caching rider locations and metrics"""

    def __init__(self):
        redis_host = getattr(Config, 'REDIS_HOST', 'localhost')
        redis_port = getattr(Config, 'REDIS_PORT', 6379)
        redis_db = getattr(Config, 'REDIS_DB', 0)

        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True
            )
            self.redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using fallback mode.")
            self.redis_client = None

    def set_rider_location(self, rider_id, latitude, longitude, expiry=300):
        """
        Store rider location in Redis with expiry (default 5 minutes)
        """
        if not self.redis_client:
            return False

        try:
            key = f"rider:location:{rider_id}"
            data = {
                'latitude': latitude,
                'longitude': longitude,
                'timestamp': timezone.now().isoformat()
            }
            self.redis_client.setex(key, expiry, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Failed to set rider location in Redis: {e}")
            return False

    def get_rider_location(self, rider_id):
        """
        Get rider location from Redis
        """
        if not self.redis_client:
            return None

        try:
            key = f"rider:location:{rider_id}"
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get rider location from Redis: {e}")
            return None

    def get_active_riders(self, warehouse_id):
        """
        Get all active riders for a warehouse (riders with location in Redis)
        """
        if not self.redis_client:
            return []

        try:
            pattern = f"rider:location:*"
            active_riders = []

            for key in self.redis_client.scan_iter(pattern):
                rider_id = key.split(':')[-1]
                location_data = self.get_rider_location(rider_id)
                if location_data:
                    active_riders.append({
                        'rider_id': int(rider_id),
                        'latitude': location_data['latitude'],
                        'longitude': location_data['longitude'],
                        'last_update': location_data['timestamp']
                    })

            return active_riders
        except Exception as e:
            logger.error(f"Failed to get active riders: {e}")
            return []

    def cache_rider_metrics(self, rider_id, metrics, expiry=3600):
        """
        Cache rider performance metrics (1 hour expiry)
        """
        if not self.redis_client:
            return False

        try:
            key = f"rider:metrics:{rider_id}"
            self.redis_client.setex(key, expiry, json.dumps(metrics))
            return True
        except Exception as e:
            logger.error(f"Failed to cache rider metrics: {e}")
            return False

    def get_rider_metrics(self, rider_id):
        """
        Get cached rider metrics
        """
        if not self.redis_client:
            return None

        try:
            key = f"rider:metrics:{rider_id}"
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get rider metrics: {e}")
            return None


class LocationTrackingService:
    """Service for tracking and validating rider locations"""

    # Thresholds for suspicious activity detection
    MAX_SPEED_KMH = 120  # Maximum reasonable speed
    MAX_JUMP_DISTANCE_KM = 50  # Maximum distance jump between updates

    @staticmethod
    def calculate_distance(point1, point2):
        """
        Calculate distance between two points in kilometers using PostGIS
        """
        from django.contrib.gis.geos import Point
        from django.contrib.gis.measure import D

        if not point1 or not point2:
            return None

        # Distance in meters, convert to km
        distance_m = point1.distance(point2) * 100  # Geography distance in meters
        return distance_m / 1000

    @staticmethod
    def calculate_speed(distance_km, time_delta_seconds):
        """
        Calculate speed in km/h
        """
        if time_delta_seconds == 0:
            return 0

        hours = time_delta_seconds / 3600
        return distance_km / hours if hours > 0 else 0

    @staticmethod
    def is_suspicious_movement(distance_km, speed_kmh):
        """
        Check if movement is suspicious based on distance and speed
        """
        if distance_km and distance_km > LocationTrackingService.MAX_JUMP_DISTANCE_KM:
            return True

        if speed_kmh and speed_kmh > LocationTrackingService.MAX_SPEED_KMH:
            return True

        return False

    @staticmethod
    def update_location_with_tracking(rider, latitude, longitude):
        """
        Update rider location and create history entry with security checks
        """
        from .models import RiderLocationHistory

        new_location = Point(longitude, latitude, srid=4326)

        # Calculate metrics if previous location exists
        distance_km = None
        speed_kmh = None
        is_suspicious = False

        if rider.current_location:
            # Get the last location history entry
            last_history = RiderLocationHistory.objects.filter(rider=rider).first()

            if last_history:
                time_delta = (timezone.now() - last_history.timestamp).total_seconds()

                if time_delta > 0:
                    distance_km = LocationTrackingService.calculate_distance(
                        rider.current_location, new_location
                    )

                    if distance_km:
                        speed_kmh = LocationTrackingService.calculate_speed(
                            distance_km, time_delta
                        )
                        is_suspicious = LocationTrackingService.is_suspicious_movement(
                            distance_km, speed_kmh
                        )

        # Update rider location
        rider.current_location = new_location
        rider.save()

        # Create history entry
        history = RiderLocationHistory.objects.create(
            rider=rider,
            location=new_location,
            speed_kmh=speed_kmh,
            distance_from_previous_km=distance_km,
            is_suspicious=is_suspicious
        )

        # Cache in Redis
        redis_service = RedisService()
        redis_service.set_rider_location(rider.id, latitude, longitude)

        return {
            'updated': True,
            'is_suspicious': is_suspicious,
            'speed_kmh': speed_kmh,
            'distance_km': distance_km
        }


class EarningsService:
    """Service for calculating rider earnings and statistics"""

    @staticmethod
    def get_earnings_summary(rider, start_date=None, end_date=None):
        """
        Get earnings summary for a rider within date range
        """
        from warehouses.models import RiderPayout

        payouts = RiderPayout.objects.filter(rider=rider)

        if start_date:
            payouts = payouts.filter(created_at__gte=start_date)
        if end_date:
            payouts = payouts.filter(created_at__lte=end_date)

        completed_payouts = payouts.filter(status='completed')

        total_earnings = completed_payouts.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')

        total_distance = completed_payouts.aggregate(
            total=Sum('distance_km')
        )['total'] or Decimal('0.00')

        completed_orders = completed_payouts.count()

        return {
            'total_earnings': float(total_earnings),
            'completed_orders_count': completed_orders,
            'total_distance_km': float(total_distance)
        }

    @staticmethod
    def get_earnings_by_period(rider, period='daily', start_date=None, end_date=None):
        """
        Get earnings grouped by period (daily, weekly, monthly)
        """
        from warehouses.models import RiderPayout
        from django.db.models.functions import TruncDate, TruncWeek, TruncMonth

        payouts = RiderPayout.objects.filter(
            rider=rider,
            status='completed'
        )

        if start_date:
            payouts = payouts.filter(created_at__gte=start_date)
        if end_date:
            payouts = payouts.filter(created_at__lte=end_date)

        trunc_func = {
            'daily': TruncDate,
            'weekly': TruncWeek,
            'monthly': TruncMonth,
        }.get(period, TruncDate)

        grouped = payouts.annotate(
            period=trunc_func('created_at')
        ).values('period').annotate(
            earnings=Sum('total_amount'),
            orders=Count('id'),
            distance=Sum('distance_km')
        ).order_by('-period')

        return list(grouped)


class PerformanceMetricsService:
    """Service for calculating rider performance metrics"""

    @staticmethod
    def calculate_performance_metrics(rider, start_date=None, end_date=None):
        """
        Calculate comprehensive performance metrics for a rider
        """
        from orders.models import Order
        from delivery.models import Delivery

        deliveries = Delivery.objects.filter(rider=rider.user)

        if start_date:
            deliveries = deliveries.filter(created_at__gte=start_date)
        if end_date:
            deliveries = deliveries.filter(created_at__lte=end_date)

        # Calculate average delivery time
        completed_deliveries = deliveries.filter(status='delivered')

        total_time = timedelta()
        delivery_count = 0

        for delivery in completed_deliveries:
            if delivery.delivered_at and delivery.created_at:
                total_time += (delivery.delivered_at - delivery.created_at)
                delivery_count += 1

        avg_delivery_time_minutes = None
        if delivery_count > 0:
            avg_delivery_time_minutes = total_time.total_seconds() / 60 / delivery_count

        # Calculate success rate
        total_deliveries = deliveries.count()
        successful_deliveries = completed_deliveries.count()
        success_rate = (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0

        # Calculate distance per order
        from warehouses.models import RiderPayout
        payouts = RiderPayout.objects.filter(rider=rider, status='completed')

        if start_date:
            payouts = payouts.filter(created_at__gte=start_date)
        if end_date:
            payouts = payouts.filter(created_at__lte=end_date)

        total_distance = payouts.aggregate(total=Sum('distance_km'))['total'] or Decimal('0.00')
        distance_per_order = (total_distance / successful_deliveries) if successful_deliveries > 0 else Decimal('0.00')

        return {
            'average_delivery_time_minutes': round(avg_delivery_time_minutes, 2) if avg_delivery_time_minutes else None,
            'success_rate': round(success_rate, 2),
            'total_deliveries': total_deliveries,
            'successful_deliveries': successful_deliveries,
            'distance_per_order': float(distance_per_order),
            'total_distance_km': float(total_distance)
        }

    @staticmethod
    def get_monthly_aggregates(rider):
        """
        Get monthly performance aggregates
        """
        from django.db.models.functions import TruncMonth
        from delivery.models import Delivery

        # Get last 6 months of data
        six_months_ago = timezone.now() - timedelta(days=180)

        deliveries = Delivery.objects.filter(
            rider=rider.user,
            created_at__gte=six_months_ago
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total_deliveries=Count('id'),
            completed=Count('id', filter=Q(status='delivered'))
        ).order_by('-month')

        return list(deliveries)


class NotificationService:
    """Service for managing rider notifications"""

    @staticmethod
    def create_notification(rider, notification_type, title, message, metadata=None):
        """
        Create a notification for a rider
        """
        from .models import RiderNotification

        notification = RiderNotification.objects.create(
            rider=rider,
            notification_type=notification_type,
            title=title,
            message=message,
            metadata=metadata or {}
        )

        # TODO: Integrate with Supabase Edge Functions for push notifications
        # This would be implemented based on Supabase setup

        return notification

    @staticmethod
    def send_order_assigned_notification(rider, order):
        """
        Send notification when order is assigned to rider
        """
        return NotificationService.create_notification(
            rider=rider,
            notification_type='order_assigned',
            title='New Order Assigned',
            message=f'You have been assigned order #{order.id}',
            metadata={'order_id': order.id}
        )

    @staticmethod
    def send_order_status_notification(rider, order, status):
        """
        Send notification when order status changes
        """
        return NotificationService.create_notification(
            rider=rider,
            notification_type='order_update',
            title='Order Status Updated',
            message=f'Order #{order.id} status changed to {status}',
            metadata={'order_id': order.id, 'status': status}
        )

