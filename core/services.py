from supabase import create_client, Client
from core.config import Config
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for handling notifications"""

    @staticmethod
    def send_notification(
        user, title: str, message: str, notification_type: str = "INFO"
    ):
        """
        Send notification to a user

        Args:
            user: User object
            title: Notification title
            message: Notification message
            notification_type: Type of notification (INFO, WARNING, ERROR, SUCCESS)
        """
        try:
            # Import here to avoid circular imports
            from shopkeepers.models import Notification

            notification = Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
            )
            logger.info(f"Notification sent to user {user.id}: {title}")
            return notification
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            return None

    @staticmethod
    def send_bulk_notification(
        users: List, title: str, message: str, notification_type: str = "INFO"
    ):
        """
        Send notification to multiple users

        Args:
            users: List of User objects
            title: Notification title
            message: Notification message
            notification_type: Type of notification
        """
        try:
            from shopkeepers.models import Notification

            notifications = [
                Notification(
                    user=user,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                )
                for user in users
            ]
            created = Notification.objects.bulk_create(notifications)
            logger.info(f"Bulk notification sent to {len(created)} users")
            return created
        except Exception as e:
            logger.error(f"Failed to send bulk notification: {str(e)}")
            return []


class InventoryService:
    """Service for inventory management operations"""

    @staticmethod
    def check_availability(warehouse, items_data):
        """
        Check if all items are available in the warehouse

        Args:
            warehouse: Warehouse object
            items_data: List of dicts with 'item_id' and 'quantity'

        Returns:
            Tuple of (is_available: bool, error_message: str or None)
        """
        try:
            from inventory.models import Item

            for item_data in items_data:
                item_id = item_data.get("item_id")
                quantity = item_data.get("quantity")

                try:
                    item = Item.objects.get(id=item_id, warehouse=warehouse)
                    if item.quantity < quantity:
                        return (
                            False,
                            f"Insufficient stock for {item.name}. Available: {item.quantity}, Requested: {quantity}",
                        )
                except Item.DoesNotExist:
                    return False, f"Item with ID {item_id} not found in this warehouse"

            return True, None
        except Exception as e:
            logger.error(f"Error checking availability: {str(e)}")
            return False, f"Error checking availability: {str(e)}"

    @staticmethod
    def check_stock_availability(item_id: int, quantity: int) -> bool:
        """
        Check if sufficient stock is available

        Args:
            item_id: Item ID
            quantity: Requested quantity

        Returns:
            True if stock available, False otherwise
        """
        try:
            from inventory.models import Item

            item = Item.objects.get(id=item_id)
            return item.stock_quantity >= quantity
        except Exception as e:
            logger.error(f"Error checking stock availability: {str(e)}")
            return False

    @staticmethod
    def update_stock(item_id: int, quantity_change: int):
        """
        Update item stock quantity

        Args:
            item_id: Item ID
            quantity_change: Amount to add (positive) or subtract (negative)
        """
        try:
            from inventory.models import Item
            from django.db.models import F

            item = Item.objects.get(id=item_id)
            item.stock_quantity = F("stock_quantity") + quantity_change
            item.save()
            item.refresh_from_db()

            logger.info(f"Stock updated for item {item_id}: {quantity_change}")
            return item
        except Exception as e:
            logger.error(f"Error updating stock: {str(e)}")
            raise


class SupabaseService:
    """Service for interacting with Supabase Auth"""

    _client: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client"""
        if cls._client is None:
            Config.validate()
            cls._client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        return cls._client

    @classmethod
    def send_otp(cls, email: str) -> Dict[str, Any]:
        """
        Send OTP to email (6-digit code, not magic link)

        Args:
            email: Email address

        Returns:
            Response from Supabase
        """
        try:
            client = cls.get_client()
            logger.debug(f"Attempting to send OTP to email: {email}")

            # Send OTP code (not magic link) to email
            # The user will receive a 6-digit code to enter manually
            response = client.auth.sign_in_with_otp(
                {
                    "email": email,
                    "options": {
                        "should_create_user": True,
                        "email_redirect_to": None,  # Disable redirect URL
                    },
                }
            )
            logger.info(f"OTP code sent successfully to {email}")
            return {"success": True, "message": "OTP sent successfully"}
        except Exception as e:
            logger.error(f"Failed to send OTP to {email}: {str(e)}", exc_info=True)
            raise Exception(f"Failed to send OTP: {str(e)}")

    @classmethod
    def verify_otp(cls, email: str, token: str) -> Dict[str, Any]:
        """
        Verify OTP for email

        Args:
            email: Email address
            token: OTP token received via email

        Returns:
            User session data from Supabase
        """
        try:
            client = cls.get_client()
            logger.debug(f"Attempting to verify OTP for email: {email}")

            response = client.auth.verify_otp(
                {"email": email, "token": token, "type": "email"}
            )
            logger.info(f"OTP verified successfully for {email}")
            return response
        except Exception as e:
            logger.error(f"Failed to verify OTP for {email}: {str(e)}", exc_info=True)
            raise Exception(f"Invalid or expired OTP: {str(e)}")

    @classmethod
    def sign_out(cls, access_token: str) -> Dict[str, Any]:
        """
        Sign out user

        Args:
            access_token: User's access token

        Returns:
            Success response
        """
        try:
            client = cls.get_client()
            logger.debug(f"Attempting to sign out user")

            # Set the session with the access token
            client.auth.set_session(access_token, access_token)
            client.auth.sign_out()
            logger.info("User signed out successfully")
            return {"success": True, "message": "Signed out successfully"}
        except Exception as e:
            logger.error(f"Failed to sign out: {str(e)}", exc_info=True)
            raise Exception(f"Sign out failed: {str(e)}")

    @classmethod
    def get_user(cls, access_token: str) -> Dict[str, Any]:
        """
        Get user details from access token

        Args:
            access_token: User's access token

        Returns:
            User data from Supabase
        """
        try:
            client = cls.get_client()
            logger.debug(f"Attempting to get user from access token")

            response = client.auth.get_user(access_token)
            logger.debug(f"Successfully retrieved user data")
            return response
        except Exception as e:
            logger.error(f"Failed to get user: {str(e)}", exc_info=True)
            raise Exception(f"Failed to get user: {str(e)}")
