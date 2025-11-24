from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from notifications.models import Notification

User = get_user_model()


class NotificationModelTests(TestCase):
    """Test cases for Notification model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", role="SHOPKEEPER"
        )

    def test_create_notification(self):
        """Test creating a notification"""
        notification = Notification.objects.create(
            user=self.user,
            title="Test Notification",
            message="This is a test message",
            type="order_update",
        )
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, "Test Notification")
        self.assertEqual(notification.message, "This is a test message")
        self.assertEqual(notification.type, "order_update")
        self.assertFalse(notification.is_read)

    def test_notification_default_is_read(self):
        """Test notification default is_read is False"""
        notification = Notification.objects.create(
            user=self.user, title="Test", message="Test message", type="system"
        )
        self.assertFalse(notification.is_read)

    def test_notification_type_choices(self):
        """Test valid notification type choices"""
        valid_types = ["order_update", "payment", "system"]
        for notif_type in valid_types:
            notification = Notification.objects.create(
                user=self.user,
                title=f"Test {notif_type}",
                message="Test message",
                type=notif_type,
            )
            self.assertEqual(notification.type, notif_type)

    def test_notification_mark_as_read(self):
        """Test marking notification as read"""
        notification = Notification.objects.create(
            user=self.user, title="Test", message="Test message", type="system"
        )
        notification.is_read = True
        notification.save()
        self.assertTrue(notification.is_read)

    def test_notification_string_representation(self):
        """Test notification string representation"""
        notification = Notification.objects.create(
            user=self.user,
            title="Test Notification",
            message="Test message",
            type="system",
        )
        self.assertIn("Test Notification", str(notification))
        self.assertIn(self.user.email, str(notification))


class NotificationViewTests(APITestCase):
    """Test cases for Notification views"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", role="SHOPKEEPER"
        )
        self.other_user = User.objects.create_user(
            email="other@example.com", role="SHOPKEEPER"
        )
        self.notification1 = Notification.objects.create(
            user=self.user,
            title="Notification 1",
            message="Message 1",
            type="order_update",
        )
        self.notification2 = Notification.objects.create(
            user=self.user,
            title="Notification 2",
            message="Message 2",
            type="payment",
            is_read=True,
        )
        self.other_notification = Notification.objects.create(
            user=self.other_user,
            title="Other Notification",
            message="Other Message",
            type="system",
        )
        self.client = APIClient()


class NotificationPermissionTests(TestCase):
    """Test cases for notification permissions"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", role="SHOPKEEPER"
        )
        self.other_user = User.objects.create_user(
            email="other@example.com", role="SHOPKEEPER"
        )
        self.notification = Notification.objects.create(
            user=self.user, title="Test", message="Test message", type="system"
        )

    def test_notification_belongs_to_user(self):
        """Test notification belongs to correct user"""
        self.assertEqual(self.notification.user, self.user)

    def test_notification_cannot_be_accessed_by_other_user(self):
        """Test notification cannot be accessed by another user"""
        self.assertNotEqual(self.notification.user, self.other_user)


class NotificationFilterTests(TestCase):
    """Test cases for notification filtering"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", role="SHOPKEEPER"
        )
        self.read_notification = Notification.objects.create(
            user=self.user,
            title="Read Notification",
            message="Message",
            type="system",
            is_read=True,
        )
        self.unread_notification = Notification.objects.create(
            user=self.user,
            title="Unread Notification",
            message="Message",
            type="order_update",
            is_read=False,
        )

    def test_filter_unread_notifications(self):
        """Test filtering unread notifications"""
        unread = Notification.objects.filter(user=self.user, is_read=False)
        self.assertEqual(unread.count(), 1)
        self.assertEqual(unread.first(), self.unread_notification)

    def test_filter_read_notifications(self):
        """Test filtering read notifications"""
        read = Notification.objects.filter(user=self.user, is_read=True)
        self.assertEqual(read.count(), 1)
        self.assertEqual(read.first(), self.read_notification)

    def test_filter_by_type(self):
        """Test filtering notifications by type"""
        order_updates = Notification.objects.filter(user=self.user, type="order_update")
        self.assertEqual(order_updates.count(), 1)
        self.assertEqual(order_updates.first().type, "order_update")


class NotificationBulkOperationsTests(TestCase):
    """Test cases for notification bulk operations"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", role="SHOPKEEPER"
        )
        # Create multiple unread notifications
        for i in range(5):
            Notification.objects.create(
                user=self.user,
                title=f"Notification {i}",
                message=f"Message {i}",
                type="system",
                is_read=False,
            )

    def test_mark_all_as_read(self):
        """Test marking all notifications as read"""
        unread_count = Notification.objects.filter(
            user=self.user, is_read=False
        ).count()
        self.assertEqual(unread_count, 5)

        Notification.objects.filter(user=self.user).update(is_read=True)

        unread_count = Notification.objects.filter(
            user=self.user, is_read=False
        ).count()
        self.assertEqual(unread_count, 0)

    def test_delete_old_notifications(self):
        """Test deleting notifications"""
        initial_count = Notification.objects.filter(user=self.user).count()
        self.assertEqual(initial_count, 5)

        # Delete all notifications
        Notification.objects.filter(user=self.user).delete()

        final_count = Notification.objects.filter(user=self.user).count()
        self.assertEqual(final_count, 0)
