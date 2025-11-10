"""
Celery tasks for payment and payout processing
"""
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
    name="payouts.compute_for_order"
)
def compute_payout_for_order(self, order_id):
    """
    Compute and create payout for a delivered order.

    Args:
        order_id: ID of the delivered order

    Returns:
        dict: Task result with payout_id and status
    """
    from orders.models import Order
    from delivery.models import Delivery
    from payments.models import Payout

    try:
        with transaction.atomic():
            # Get order
            try:
                order = Order.objects.select_related('warehouse').get(id=order_id)
            except Order.DoesNotExist:
                logger.error(f"Order {order_id} not found for payout computation")
                return {
                    "success": False,
                    "error": "Order not found",
                    "order_id": order_id
                }

            # Validate order is delivered
            if order.status != "delivered":
                logger.warning(f"Order {order_id} is not delivered, cannot compute payout")
                return {
                    "success": False,
                    "error": "Order not delivered",
                    "order_id": order_id
                }

            # Get delivery record
            try:
                delivery = Delivery.objects.select_related('rider').get(order=order)
            except Delivery.DoesNotExist:
                logger.error(f"No delivery record found for order {order_id}")
                return {
                    "success": False,
                    "error": "No delivery record found",
                    "order_id": order_id
                }

            # Check if payout already exists
            if Payout.objects.filter(rider=delivery.rider, warehouse=order.warehouse).exists():
                # Check if we should add to existing payout or skip
                logger.info(f"Payout may already exist for rider {delivery.rider.id} and warehouse {order.warehouse.id}")

            # Calculate distance (assuming delivery model has distance field)
            # If not, we'll use a default or compute from PostGIS
            distance_km = getattr(delivery, 'distance_km', 0.0)

            # Default rate per km
            rate_per_km = Decimal("10.00")

            # Compute payout amount
            computed_amount = Decimal(str(distance_km)) * rate_per_km

            # Create payout record
            payout = Payout.objects.create(
                rider=delivery.rider,
                warehouse=order.warehouse,
                total_distance=distance_km,
                rate_per_km=rate_per_km,
                computed_amount=computed_amount,
                status="pending"
            )

            logger.info(
                f"Payout {payout.id} created for order {order_id}: "
                f"Rider {delivery.rider.id}, Amount {computed_amount}"
            )

            # Send notification to rider
            notify_payout_creation.delay(payout.id)

            return {
                "success": True,
                "payout_id": payout.id,
                "order_id": order_id,
                "rider_id": delivery.rider.id,
                "amount": float(computed_amount)
            }

    except Exception as e:
        logger.error(
            f"Failed to compute payout for order {order_id}: {str(e)}",
            exc_info=True
        )
        raise


@shared_task(
    bind=True,
    name="payouts.nightly_rollup"
)
def nightly_payout_rollup(self):
    """
    Nightly task to aggregate and settle all pending payouts for each warehouse.
    Marks completed payouts as settled.

    Returns:
        dict: Task result with aggregated stats
    """
    from payments.models import Payout
    from warehouses.models import Warehouse
    from django.db.models import Sum, Count

    try:
        # Get all warehouses with pending payouts
        warehouses_with_payouts = Payout.objects.filter(
            status="pending"
        ).values_list('warehouse', flat=True).distinct()

        results = []

        for warehouse_id in warehouses_with_payouts:
            with transaction.atomic():
                # Aggregate pending payouts for this warehouse
                stats = Payout.objects.filter(
                    warehouse_id=warehouse_id,
                    status="pending"
                ).aggregate(
                    total_amount=Sum('computed_amount'),
                    total_payouts=Count('id'),
                    total_distance=Sum('total_distance')
                )

                # Mark all pending payouts as settled
                updated_count = Payout.objects.filter(
                    warehouse_id=warehouse_id,
                    status="pending"
                ).update(
                    status="settled",
                    updated_at=timezone.now()
                )

                warehouse_result = {
                    "warehouse_id": warehouse_id,
                    "total_amount": float(stats['total_amount'] or 0),
                    "total_payouts": stats['total_payouts'],
                    "total_distance": float(stats['total_distance'] or 0),
                    "settled_count": updated_count
                }

                results.append(warehouse_result)

                logger.info(
                    f"Warehouse {warehouse_id}: Settled {updated_count} payouts, "
                    f"Total amount: {stats['total_amount']}"
                )

                # Send notification to warehouse
                notify_payout_settlement.delay(warehouse_id, warehouse_result)

        return {
            "success": True,
            "timestamp": timezone.now().isoformat(),
            "warehouses_processed": len(results),
            "results": results
        }

    except Exception as e:
        logger.error(f"Failed to complete nightly payout rollup: {str(e)}", exc_info=True)
        raise


@shared_task(
    bind=True,
    name="payouts.notify_completion"
)
def notify_payout_completion(self, payout_id, success=True):
    """
    Send notification when payout is completed or failed.

    Args:
        payout_id: ID of the payout
        success: Whether payout was successful

    Returns:
        dict: Task result
    """
    from payments.models import Payout
    from notifications.tasks import send_notification_task

    try:
        payout = Payout.objects.select_related('rider', 'warehouse').get(id=payout_id)

        if success:
            title = "Payout Completed"
            message = f"Your payout of ₹{payout.computed_amount} has been completed."
            notification_type = "payout_success"
        else:
            title = "Payout Failed"
            message = f"Your payout of ₹{payout.computed_amount} has failed. Please contact support."
            notification_type = "payout_failure"

        # Send notification to rider
        send_notification_task.delay(
            user_id=payout.rider.user.id,
            title=title,
            message=message,
            notification_type=notification_type
        )

        logger.info(f"Notification sent for payout {payout_id}, success={success}")

        return {
            "success": True,
            "payout_id": payout_id,
            "notification_type": notification_type
        }

    except Payout.DoesNotExist:
        logger.error(f"Payout {payout_id} not found for notification")
        return {
            "success": False,
            "error": "Payout not found",
            "payout_id": payout_id
        }
    except Exception as e:
        logger.error(f"Failed to send payout notification: {str(e)}", exc_info=True)
        raise


@shared_task(name="payouts.notify_creation")
def notify_payout_creation(payout_id):
    """
    Send notification when payout is created.

    Args:
        payout_id: ID of the newly created payout
    """
    from payments.models import Payout
    from notifications.tasks import send_notification_task

    try:
        payout = Payout.objects.select_related('rider', 'warehouse').get(id=payout_id)

        send_notification_task.delay(
            user_id=payout.rider.user.id,
            title="New Payout Pending",
            message=f"A payout of ₹{payout.computed_amount} for {payout.total_distance}km has been created.",
            notification_type="payout_created"
        )

        logger.info(f"Creation notification sent for payout {payout_id}")

    except Exception as e:
        logger.error(f"Failed to send payout creation notification: {str(e)}")


@shared_task(name="payouts.notify_settlement")
def notify_payout_settlement(warehouse_id, stats):
    """
    Send notification to warehouse when daily settlement is complete.

    Args:
        warehouse_id: ID of the warehouse
        stats: Dictionary with settlement statistics
    """
    from notifications.tasks import send_notification_task
    from warehouses.models import Warehouse

    try:
        warehouse = Warehouse.objects.get(id=warehouse_id)

        send_notification_task.delay(
            user_id=warehouse.admin.id,
            title="Daily Payout Settlement Complete",
            message=f"Settled {stats['settled_count']} payouts totaling ₹{stats['total_amount']}.",
            notification_type="settlement_complete"
        )

        logger.info(f"Settlement notification sent for warehouse {warehouse_id}")

    except Exception as e:
        logger.error(f"Failed to send settlement notification: {str(e)}")

