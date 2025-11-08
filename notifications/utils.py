"""
Utility functions for sending notifications
"""
from notifications.tasks import send_notification_task
import logging

logger = logging.getLogger(__name__)


def send_notification(user_id, title, message, notification_type="system"):
    """
    Send notification to a user by enqueuing Celery task

    Args:
        user_id: ID of the user to notify
        title: Notification title
        message: Notification message
        notification_type: Type of notification (order_update, payment, system)

    Returns:
        AsyncResult: Celery task result
    """
    # Validate notification type
    valid_types = ["order_update", "payment", "system"]
    if notification_type not in valid_types:
        logger.warning(f"Invalid notification type: {notification_type}, using 'system'")
        notification_type = "system"

    # Enqueue task to notifications queue
    task = send_notification_task.apply_async(
        args=[user_id, title, message, notification_type],
        queue="notifications",
        retry=True
    )

    logger.info(
        f"Notification task enqueued for user {user_id}: {task.id}"
    )

    return task


def send_order_update_notification(user_id, order_id, status, additional_info=""):
    """
    Send order update notification

    Args:
        user_id: ID of the user
        order_id: ID of the order
        status: New order status
        additional_info: Additional information
    """
    title = f"Order #{order_id} Update"
    message = f"Your order status has been updated to: {status}. {additional_info}"

    return send_notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type="order_update"
    )


def send_rider_assignment_notification(user_id, order_id, rider_name):
    """
    Send notification when rider is assigned to order

    Args:
        user_id: ID of the user (shopkeeper)
        order_id: ID of the order
        rider_name: Name of the assigned rider
    """
    title = f"Rider Assigned to Order #{order_id}"
    message = f"Rider {rider_name} has been assigned to your order."

    return send_notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type="order_update"
    )


def send_payment_notification(user_id, payment_id, amount, status):
    """
    Send payment notification

    Args:
        user_id: ID of the user
        payment_id: ID of the payment
        amount: Payment amount
        status: Payment status
    """
    title = "Payment Update"
    message = f"Payment #{payment_id} of ₹{amount} has been {status}."

    return send_notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type="payment"
    )


def send_system_notification(user_id, title, message):
    """
    Send generic system notification

    Args:
        user_id: ID of the user
        title: Notification title
        message: Notification message
    """
    return send_notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type="system"
    )

