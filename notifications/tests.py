"""
Tests for notification system
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from notifications.models import Notification
from notifications.tasks import send_notification_task
from unittest.mock import patch, MagicMock

User = get_user_model()


class NotificationModelTest(TestCase):
    """Test Notification model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )

    def test_create_notification(self):
        """Test creating a notification"""
        notification = Notification.objects.create(
            user=self.user,
            title="Test Notification",
            message="Test message",
            type="system"
        )

        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, "Test Notification")
        self.assertEqual(notification.type, "system")
        self.assertFalse(notification.is_read)

    def test_notification_ordering(self):
        """Test notifications are ordered by created_at descending"""
        notif1 = Notification.objects.create(
            user=self.user,
            title="First",
            message="First message",
            type="system"
        )
        notif2 = Notification.objects.create(
            user=self.user,
            title="Second",
            message="Second message",
            type="system"
        )

        notifications = Notification.objects.all()
        self.assertEqual(notifications[0].id, notif2.id)
        self.assertEqual(notifications[1].id, notif1.id)


class NotificationAPITest(APITestCase):
    """Test notification API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123"
        )

        # Create test notifications
        self.notification1 = Notification.objects.create(
            user=self.user,
            title="Notification 1",
            message="Message 1",
            type="order_update"
        )
        self.notification2 = Notification.objects.create(
            user=self.user,
            title="Notification 2",
            message="Message 2",
            type="payment",
            is_read=True
        )
        self.notification3 = Notification.objects.create(
            user=self.other_user,
            title="Other User Notification",
            message="Message 3",
            type="system"
        )

    def test_list_notifications_unauthenticated(self):
        """Test that unauthenticated users cannot access notifications"""
        response = self.client.get("/api/notifications/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_notifications_authenticated(self):
        """Test listing notifications for authenticated user"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/notifications/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)  # Only user's notifications

        # Check unread comes first
        results = response.data["results"]
        self.assertFalse(results[0]["is_read"])
        self.assertTrue(results[1]["is_read"])

    def test_mark_single_notification_as_read(self):
        """Test marking a single notification as read"""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            "/api/notifications/read/",
            {"notification_id": self.notification1.id}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

        # Verify notification is marked as read
        self.notification1.refresh_from_db()
        self.assertTrue(self.notification1.is_read)

    def test_mark_all_notifications_as_read(self):
        """Test marking all notifications as read"""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            "/api/notifications/read/",
            {"mark_all": True}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

        # Verify all user's notifications are marked as read
        unread_count = Notification.objects.filter(
            user=self.user,
            is_read=False
        ).count()
        self.assertEqual(unread_count, 0)

    def test_cannot_mark_other_users_notification(self):
        """Test user cannot mark another user's notification as read"""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            "/api/notifications/read/",
            {"notification_id": self.notification3.id}
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_mark_read_validation_error(self):
        """Test validation error when neither notification_id nor mark_all is provided"""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch("/api/notifications/read/", {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class NotificationTaskTest(TestCase):
    """Test Celery tasks"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )

    @patch('notifications.tasks._trigger_edge_function_delivery')
    def test_send_notification_task_success(self, mock_edge_function):
        """Test successful notification task execution"""
        result = send_notification_task(
            user_id=self.user.id,
            title="Test Title",
            message="Test Message",
            notification_type="system"
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["user_id"], self.user.id)

        # Verify notification was created
        notification = Notification.objects.get(id=result["notification_id"])
        self.assertEqual(notification.title, "Test Title")
        self.assertEqual(notification.message, "Test Message")
        self.assertEqual(notification.type, "system")

    def test_send_notification_task_invalid_user(self):
        """Test task with invalid user_id"""
        result = send_notification_task(
            user_id=99999,
            title="Test Title",
            message="Test Message",
            notification_type="system"
        )

        self.assertFalse(result["success"])
        self.assertIn("error", result)

    @patch('requests.post')
    def test_edge_function_delivery_failure(self, mock_post):
        """Test that edge function failure doesn't break the task"""
        from notifications.tasks import _trigger_edge_function_delivery
        from django.conf import settings

        # Mock settings
        settings.SUPABASE_EDGE_FUNCTION_URL = "https://example.com/function"
        settings.SUPABASE_SERVICE_ROLE_KEY = "test-key"

        # Mock failed HTTP request
        mock_post.side_effect = Exception("Network error")

        notification = Notification.objects.create(
            user=self.user,
            title="Test",
            message="Test",
            type="system"
        )

        # Should not raise exception
        try:
            _trigger_edge_function_delivery(notification, self.user)
        except Exception:
            self.fail("Edge function failure should not raise exception")


class NotificationUtilsTest(TestCase):
    """Test notification utility functions"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )

    @patch('notifications.utils.send_notification_task')
    def test_send_order_update_notification(self, mock_task):
        """Test sending order update notification"""
        from notifications.utils import send_order_update_notification

        mock_task.apply_async = MagicMock()

        send_order_update_notification(
            user_id=self.user.id,
            order_id=123,
            status="confirmed"
        )

        mock_task.apply_async.assert_called_once()
        call_args = mock_task.apply_async.call_args

        self.assertEqual(call_args[1]["args"][0], self.user.id)
        self.assertIn("Order #123", call_args[1]["args"][1])
        self.assertEqual(call_args[1]["args"][3], "order_update")

    @patch('notifications.utils.send_notification_task')
    def test_send_payment_notification(self, mock_task):
        """Test sending payment notification"""
        from notifications.utils import send_payment_notification

        mock_task.apply_async = MagicMock()

        send_payment_notification(
            user_id=self.user.id,
            payment_id=456,
            amount=1000,
            status="completed"
        )

        mock_task.apply_async.assert_called_once()
        call_args = mock_task.apply_async.call_args

        self.assertEqual(call_args[1]["args"][3], "payment")

