"""
Celery tasks for notification processing
"""
from celery import shared_task
from django.conf import settings
from notifications.models import Notification
from accounts.models import User
import logging
import requests

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
    name="notifications.send_notification"
)
def send_notification_task(self, user_id, title, message, notification_type):
    """
    Process notification task - save to DB and optionally trigger external delivery

    Args:
        user_id: ID of the user to notify
        title: Notification title
        message: Notification message
        notification_type: Type of notification (order_update, payment, system)

    Returns:
        dict: Task result with notification_id and status
    """
    try:
        # Validate user exists
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found for notification")
            return {
                "success": False,
                "error": "User not found",
                "user_id": user_id
            }

        # Create notification in database
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            type=notification_type
        )

        logger.info(
            f"Notification {notification.id} created for user {user_id}: {title}"
        )

        # Optionally trigger Supabase Edge Function for push/SMS delivery
        if hasattr(settings, "SUPABASE_EDGE_FUNCTION_URL") and settings.SUPABASE_EDGE_FUNCTION_URL:
            try:
                _trigger_edge_function_delivery(notification, user)
            except Exception as e:
                # Log but don't fail the task if edge function fails
                logger.warning(
                    f"Edge function delivery failed for notification {notification.id}: {str(e)}"
                )

        return {
            "success": True,
            "notification_id": notification.id,
            "user_id": user_id,
            "type": notification_type
        }

    except Exception as e:
        logger.error(
            f"Failed to process notification for user {user_id}: {str(e)}",
            exc_info=True
        )
        # Re-raise to trigger Celery retry mechanism
        raise


def _trigger_edge_function_delivery(notification, user):
    """
    Trigger Supabase Edge Function for push/SMS delivery

    Args:
        notification: Notification instance
        user: User instance
    """
    edge_function_url = settings.SUPABASE_EDGE_FUNCTION_URL
    service_key = settings.SUPABASE_SERVICE_ROLE_KEY

    payload = {
        "notification_id": notification.id,
        "user_id": user.id,
        "user_email": user.email,
        "title": notification.title,
        "message": notification.message,
        "type": notification.type
    }

    headers = {
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        edge_function_url,
        json=payload,
        headers=headers,
        timeout=10
    )

    response.raise_for_status()
    logger.info(f"Edge function triggered for notification {notification.id}")


@shared_task(name="notifications.cleanup_old_notifications")
def cleanup_old_notifications_task():
    """
    Cleanup old read notifications (older than 90 days)
    This can be scheduled as a periodic task
    """
    from django.utils import timezone
    from datetime import timedelta

    threshold_date = timezone.now() - timedelta(days=90)

    deleted_count, _ = Notification.objects.filter(
        is_read=True,
        created_at__lt=threshold_date
    ).delete()

    logger.info(f"Cleaned up {deleted_count} old notifications")

    return {
        "success": True,
        "deleted_count": deleted_count
    }

