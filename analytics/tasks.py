# analytics/tasks.py
from celery import shared_task
from django.db.models import (
    Count,
    Sum,
    Avg,
    F,
    Q,
    ExpressionWrapper,
    DurationField,
)
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta, datetime
from decimal import Decimal
import logging

from .models import AnalyticsSummary
from orders.models import Order
from delivery.models import Delivery
from riders.models import Rider
from warehouses.models import Warehouse
from accounts.models import User

logger = logging.getLogger(__name__)


@shared_task(name="analytics.compute_daily_summaries")
def compute_daily_summaries(target_date=None):
    """
    Compute daily analytics summaries for all entity types.
    Runs nightly to aggregate data from Orders, Payments, Riders.
    """
    if target_date is None:
        target_date = (timezone.now() - timedelta(days=1)).date()
    elif isinstance(target_date, str):
        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

    logger.info(f"Computing daily summaries for {target_date}")

    # Compute system-wide metrics
    _compute_system_metrics(target_date)

    # Compute warehouse metrics
    _compute_warehouse_metrics(target_date)

    # Compute rider metrics
    _compute_rider_metrics(target_date)

    # Compute shopkeeper metrics
    _compute_shopkeeper_metrics(target_date)

    logger.info(f"Completed daily summaries for {target_date}")
    return f"Computed summaries for {target_date}"


def _compute_system_metrics(target_date):
    """Compute system-wide metrics."""
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())

    # Get orders for the day
    daily_orders = Order.objects.filter(
        created_at__range=[start_of_day, end_of_day]
    ).aggregate(
        total_orders=Count("id"),
        total_revenue=Coalesce(Sum("total_amount"), Decimal("0.00")),
        completed_orders=Count("id", filter=Q(status="delivered")),
        pending_orders=Count("id", filter=Q(status__in=["pending", "accepted"])),
    )

    # Get delivery metrics
    delivery_stats = Delivery.objects.filter(
        created_at__range=[start_of_day, end_of_day], status="delivered"
    ).aggregate(
        avg_delivery_time=Avg(
            ExpressionWrapper(
                F("updated_at") - F("created_at"), output_field=DurationField()
            )
        )
    )

    avg_delivery_minutes = 0.0
    if delivery_stats["avg_delivery_time"]:
        avg_delivery_minutes = delivery_stats["avg_delivery_time"].total_seconds() / 60

    # Active users (placed orders)
    active_users = (
        Order.objects.filter(created_at__range=[start_of_day, end_of_day])
        .values("shopkeeper")
        .distinct()
        .count()
    )

    # Calculate daily growth
    prev_date = target_date - timedelta(days=1)
    prev_start = datetime.combine(prev_date, datetime.min.time())
    prev_end = datetime.combine(prev_date, datetime.max.time())
    prev_orders = Order.objects.filter(created_at__range=[prev_start, prev_end]).count()

    daily_growth = 0.0
    if prev_orders > 0:
        daily_growth = (
            (daily_orders["total_orders"] - prev_orders) / prev_orders
        ) * 100

    # Active riders
    active_riders = (
        Delivery.objects.filter(created_at__range=[start_of_day, end_of_day])
        .values("rider")
        .distinct()
        .count()
    )

    # Active warehouses
    active_warehouses = (
        Order.objects.filter(created_at__range=[start_of_day, end_of_day])
        .values("warehouse")
        .distinct()
        .count()
    )

    metrics = {
        "total_orders": daily_orders["total_orders"],
        "total_revenue": float(daily_orders["total_revenue"]),
        "active_users": active_users,
        "average_delivery_time": round(avg_delivery_minutes, 2),
        "daily_growth": round(daily_growth, 2),
        "pending_orders": daily_orders["pending_orders"],
        "completed_orders": daily_orders["completed_orders"],
        "active_riders": active_riders,
        "active_warehouses": active_warehouses,
    }

    AnalyticsSummary.objects.update_or_create(
        ref_type="system", ref_id=None, date=target_date, defaults={"metrics": metrics}
    )

    logger.info(f"System metrics computed for {target_date}: {metrics}")


def _compute_warehouse_metrics(target_date):
    """Compute metrics for each warehouse."""
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())

    warehouses = Warehouse.objects.all()

    for warehouse in warehouses:
        orders_data = Order.objects.filter(
            warehouse=warehouse, created_at__range=[start_of_day, end_of_day]
        ).aggregate(
            total_orders=Count("id"),
            total_revenue=Coalesce(Sum("total_amount"), Decimal("0.00")),
            completed_orders=Count("id", filter=Q(status="delivered")),
            pending_orders=Count("id", filter=Q(status__in=["pending", "accepted"])),
            rejected_orders=Count("id", filter=Q(status="rejected")),
        )

        # Completion rate
        total = orders_data["total_orders"]
        completed = orders_data["completed_orders"]
        completion_rate = (completed / total * 100) if total > 0 else 0.0

        # Average delivery time
        delivery_stats = Delivery.objects.filter(
            order__warehouse=warehouse,
            created_at__range=[start_of_day, end_of_day],
            status="delivered",
        ).aggregate(
            avg_delivery_time=Avg(
                ExpressionWrapper(
                    F("updated_at") - F("created_at"), output_field=DurationField()
                )
            )
        )

        avg_delivery_minutes = 0.0
        if delivery_stats["avg_delivery_time"]:
            avg_delivery_minutes = (
                delivery_stats["avg_delivery_time"].total_seconds() / 60
            )

        # Active riders
        active_riders = Rider.objects.filter(
            warehouse=warehouse, status="available"
        ).count()

        metrics = {
            "total_orders": orders_data["total_orders"],
            "total_revenue": float(orders_data["total_revenue"]),
            "completion_rate": round(completion_rate, 2),
            "average_delivery_time": round(avg_delivery_minutes, 2),
            "pending_orders": orders_data["pending_orders"],
            "completed_orders": orders_data["completed_orders"],
            "rejected_orders": orders_data["rejected_orders"],
            "active_riders": active_riders,
        }

        AnalyticsSummary.objects.update_or_create(
            ref_type="warehouse",
            ref_id=warehouse.id,
            date=target_date,
            defaults={"metrics": metrics},
        )

    logger.info(f"Warehouse metrics computed for {target_date}")


def _compute_rider_metrics(target_date):
    """Compute metrics for each rider."""
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())

    riders = Rider.objects.select_related("user").all()

    for rider in riders:
        deliveries = Delivery.objects.filter(
            rider=rider.user, created_at__range=[start_of_day, end_of_day]
        )

        completed_deliveries = deliveries.filter(status="delivered").count()

        # Calculate total distance (assuming distance is tracked somewhere)
        # For now, using a placeholder
        total_distance = 0.0

        # Total earnings from delivery fees
        total_earnings = (
            deliveries.filter(status="delivered").aggregate(
                total=Coalesce(Sum("delivery_fee"), Decimal("0.00"))
            )["total"]
            or Decimal("0.00")
        )

        # Average delivery time
        delivery_stats = deliveries.filter(status="delivered").aggregate(
            avg_delivery_time=Avg(
                ExpressionWrapper(
                    F("updated_at") - F("created_at"), output_field=DurationField()
                )
            )
        )

        avg_delivery_minutes = 0.0
        if delivery_stats["avg_delivery_time"]:
            avg_delivery_minutes = (
                delivery_stats["avg_delivery_time"].total_seconds() / 60
            )

        # On-time deliveries (assuming < 30 minutes is on-time)
        on_time_count = 0
        late_count = 0
        for delivery in deliveries.filter(status="delivered"):
            duration = (delivery.updated_at - delivery.created_at).total_seconds() / 60
            if duration <= 30:
                on_time_count += 1
            else:
                late_count += 1

        on_time_ratio = (
            (on_time_count / completed_deliveries * 100)
            if completed_deliveries > 0
            else 0.0
        )

        metrics = {
            "completed_deliveries": completed_deliveries,
            "total_distance": round(total_distance, 2),
            "total_earnings": float(total_earnings),
            "average_delivery_time": round(avg_delivery_minutes, 2),
            "on_time_deliveries": on_time_count,
            "late_deliveries": late_count,
            "on_time_ratio": round(on_time_ratio, 2),
        }

        AnalyticsSummary.objects.update_or_create(
            ref_type="rider",
            ref_id=rider.id,
            date=target_date,
            defaults={"metrics": metrics},
        )

    logger.info(f"Rider metrics computed for {target_date}")


def _compute_shopkeeper_metrics(target_date):
    """Compute metrics for each shopkeeper."""
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())

    shopkeepers = User.objects.filter(role="shopkeeper")

    for shopkeeper in shopkeepers:
        orders = Order.objects.filter(
            shopkeeper=shopkeeper, created_at__range=[start_of_day, end_of_day]
        )

        orders_data = orders.aggregate(
            orders_placed=Count("id"),
            total_spent=Coalesce(Sum("total_amount"), Decimal("0.00")),
            pending_orders=Count("id", filter=Q(status__in=["pending", "accepted"])),
            completed_orders=Count("id", filter=Q(status="delivered")),
            cancelled_orders=Count("id", filter=Q(status="cancelled")),
        )

        # Most frequent warehouse
        most_frequent = (
            orders.values("warehouse__name")
            .annotate(count=Count("id"))
            .order_by("-count")
            .first()
        )
        most_frequent_warehouse = (
            most_frequent["warehouse__name"] if most_frequent else None
        )

        # Repeat rate (orders from same warehouse)
        total_orders = orders_data["orders_placed"]
        repeat_orders = 0
        if most_frequent and total_orders > 0:
            repeat_orders = most_frequent["count"]

        repeat_rate = (repeat_orders / total_orders * 100) if total_orders > 0 else 0.0

        metrics = {
            "orders_placed": orders_data["orders_placed"],
            "total_spent": float(orders_data["total_spent"]),
            "most_frequent_warehouse": most_frequent_warehouse,
            "repeat_rate": round(repeat_rate, 2),
            "pending_orders": orders_data["pending_orders"],
            "completed_orders": orders_data["completed_orders"],
            "cancelled_orders": orders_data["cancelled_orders"],
        }

        AnalyticsSummary.objects.update_or_create(
            ref_type="shopkeeper",
            ref_id=shopkeeper.id,
            date=target_date,
            defaults={"metrics": metrics},
        )

    logger.info(f"Shopkeeper metrics computed for {target_date}")


@shared_task(name="analytics.update_realtime_metrics")
def update_realtime_metrics(ref_type, ref_id=None):
    """
    Update real-time metrics for dashboards.
    Stores results in cache for fast retrieval.
    """
    today = timezone.now().date()
    cache_key = f"analytics:{ref_type}:{ref_id or 'system'}:realtime"

    if ref_type == "system":
        metrics = _get_realtime_system_metrics()
    elif ref_type == "warehouse":
        metrics = _get_realtime_warehouse_metrics(ref_id)
    elif ref_type == "rider":
        metrics = _get_realtime_rider_metrics(ref_id)
    elif ref_type == "shopkeeper":
        metrics = _get_realtime_shopkeeper_metrics(ref_id)
    else:
        logger.error(f"Invalid ref_type: {ref_type}")
        return None

    # Cache for 15 minutes
    cache.set(cache_key, metrics, timeout=900)

    logger.info(f"Updated realtime metrics for {ref_type}:{ref_id}")
    return metrics


def _get_realtime_system_metrics():
    """Get real-time system metrics."""
    today = timezone.now().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = timezone.now()

    metrics = Order.objects.filter(created_at__range=[start_of_day, end_of_day]).aggregate(
        total_orders=Count("id"),
        total_revenue=Coalesce(Sum("total_amount"), Decimal("0.00")),
        pending_orders=Count("id", filter=Q(status__in=["pending", "accepted"])),
        completed_orders=Count("id", filter=Q(status="delivered")),
    )

    metrics["total_revenue"] = float(metrics["total_revenue"])
    return metrics


def _get_realtime_warehouse_metrics(warehouse_id):
    """Get real-time warehouse metrics."""
    today = timezone.now().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = timezone.now()

    metrics = Order.objects.filter(
        warehouse_id=warehouse_id, created_at__range=[start_of_day, end_of_day]
    ).aggregate(
        total_orders=Count("id"),
        total_revenue=Coalesce(Sum("total_amount"), Decimal("0.00")),
        pending_orders=Count("id", filter=Q(status__in=["pending", "accepted"])),
        completed_orders=Count("id", filter=Q(status="delivered")),
    )

    metrics["total_revenue"] = float(metrics["total_revenue"])
    return metrics


def _get_realtime_rider_metrics(rider_id):
    """Get real-time rider metrics."""
    today = timezone.now().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = timezone.now()

    try:
        rider = Rider.objects.get(id=rider_id)
        metrics = Delivery.objects.filter(
            rider=rider.user, created_at__range=[start_of_day, end_of_day]
        ).aggregate(
            completed_deliveries=Count("id", filter=Q(status="delivered")),
            total_earnings=Coalesce(
                Sum("delivery_fee", filter=Q(status="delivered")), Decimal("0.00")
            ),
        )

        metrics["total_earnings"] = float(metrics["total_earnings"])
        return metrics
    except Rider.DoesNotExist:
        return {"completed_deliveries": 0, "total_earnings": 0.0}


def _get_realtime_shopkeeper_metrics(shopkeeper_id):
    """Get real-time shopkeeper metrics."""
    today = timezone.now().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = timezone.now()

    metrics = Order.objects.filter(
        shopkeeper_id=shopkeeper_id, created_at__range=[start_of_day, end_of_day]
    ).aggregate(
        orders_placed=Count("id"),
        total_spent=Coalesce(Sum("total_amount"), Decimal("0.00")),
        pending_orders=Count("id", filter=Q(status__in=["pending", "accepted"])),
    )

    metrics["total_spent"] = float(metrics["total_spent"])
    return metrics


@shared_task(name="analytics.compute_system_analytics")
def compute_system_analytics(target_date=None):
    """
    Compute system-wide analytics for a specific date.
    Called on-demand or scheduled.
    """
    if target_date is None:
        target_date = (timezone.now() - timedelta(days=1)).date()
    elif isinstance(target_date, str):
        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

    _compute_system_metrics(target_date)

    logger.info(f"System analytics computed for {target_date}")
    return f"System analytics computed for {target_date}"


@shared_task(name="analytics.compute_warehouse_analytics")
def compute_warehouse_analytics(warehouse_id, target_date=None):
    """
    Compute warehouse analytics for a specific date.
    Called on-demand or scheduled.
    """
    if target_date is None:
        target_date = (timezone.now() - timedelta(days=1)).date()
    elif isinstance(target_date, str):
        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())

    try:
        warehouse = Warehouse.objects.get(id=warehouse_id)

        orders_data = Order.objects.filter(
            warehouse=warehouse, created_at__range=[start_of_day, end_of_day]
        ).aggregate(
            total_orders=Count("id"),
            total_revenue=Coalesce(Sum("total_amount"), Decimal("0.00")),
            completed_orders=Count("id", filter=Q(status="delivered")),
            pending_orders=Count("id", filter=Q(status__in=["pending", "accepted"])),
            rejected_orders=Count("id", filter=Q(status="rejected")),
        )

        total = orders_data["total_orders"]
        completed = orders_data["completed_orders"]
        completion_rate = (completed / total * 100) if total > 0 else 0.0

        delivery_stats = Delivery.objects.filter(
            order__warehouse=warehouse,
            created_at__range=[start_of_day, end_of_day],
            status="delivered",
        ).aggregate(
            avg_delivery_time=Avg(
                ExpressionWrapper(
                    F("updated_at") - F("created_at"), output_field=DurationField()
                )
            )
        )

        avg_delivery_minutes = 0.0
        if delivery_stats["avg_delivery_time"]:
            avg_delivery_minutes = delivery_stats["avg_delivery_time"].total_seconds() / 60

        active_riders = Rider.objects.filter(warehouse=warehouse, status="available").count()

        metrics = {
            "warehouse_name": warehouse.name,
            "total_orders": orders_data["total_orders"],
            "total_revenue": float(orders_data["total_revenue"]),
            "completion_rate": round(completion_rate, 2),
            "average_delivery_time": round(avg_delivery_minutes, 2),
            "pending_orders": orders_data["pending_orders"],
            "completed_orders": orders_data["completed_orders"],
            "rejected_orders": orders_data["rejected_orders"],
            "active_riders": active_riders,
        }

        AnalyticsSummary.objects.update_or_create(
            ref_type="warehouse",
            ref_id=warehouse.id,
            date=target_date,
            defaults={"metrics": metrics},
        )

        logger.info(f"Warehouse {warehouse_id} analytics computed for {target_date}")
        return f"Warehouse {warehouse_id} analytics computed for {target_date}"

    except Warehouse.DoesNotExist:
        logger.error(f"Warehouse {warehouse_id} not found")
        return f"Warehouse {warehouse_id} not found"


@shared_task(name="analytics.compute_rider_analytics")
def compute_rider_analytics(rider_id, target_date=None):
    """
    Compute rider analytics for a specific date.
    Called on-demand or scheduled.
    """
    if target_date is None:
        target_date = (timezone.now() - timedelta(days=1)).date()
    elif isinstance(target_date, str):
        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())

    try:
        rider = Rider.objects.select_related("user").get(id=rider_id)

        deliveries = Delivery.objects.filter(
            rider=rider.user, created_at__range=[start_of_day, end_of_day]
        )

        completed_deliveries = deliveries.filter(status="delivered").count()
        total_distance = 0.0

        total_earnings = (
            deliveries.filter(status="delivered").aggregate(
                total=Coalesce(Sum("delivery_fee"), Decimal("0.00"))
            )["total"] or Decimal("0.00")
        )

        delivery_stats = deliveries.filter(status="delivered").aggregate(
            avg_delivery_time=Avg(
                ExpressionWrapper(
                    F("updated_at") - F("created_at"), output_field=DurationField()
                )
            )
        )

        avg_delivery_minutes = 0.0
        if delivery_stats["avg_delivery_time"]:
            avg_delivery_minutes = delivery_stats["avg_delivery_time"].total_seconds() / 60

        on_time_count = 0
        late_count = 0
        for delivery in deliveries.filter(status="delivered"):
            duration = (delivery.updated_at - delivery.created_at).total_seconds() / 60
            if duration <= 30:
                on_time_count += 1
            else:
                late_count += 1

        on_time_ratio = (on_time_count / completed_deliveries * 100) if completed_deliveries > 0 else 0.0

        metrics = {
            "rider_name": rider.user.get_full_name() if hasattr(rider.user, 'get_full_name') else str(rider.user),
            "completed_deliveries": completed_deliveries,
            "total_distance": round(total_distance, 2),
            "total_earnings": float(total_earnings),
            "average_delivery_time": round(avg_delivery_minutes, 2),
            "on_time_deliveries": on_time_count,
            "late_deliveries": late_count,
            "on_time_ratio": round(on_time_ratio, 2),
        }

        AnalyticsSummary.objects.update_or_create(
            ref_type="rider",
            ref_id=rider.id,
            date=target_date,
            defaults={"metrics": metrics},
        )

        logger.info(f"Rider {rider_id} analytics computed for {target_date}")
        return f"Rider {rider_id} analytics computed for {target_date}"

    except Rider.DoesNotExist:
        logger.error(f"Rider {rider_id} not found")
        return f"Rider {rider_id} not found"


