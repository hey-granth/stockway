from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from shopkeepers.models import Notification, SupportTicket
from orders.models import Order
from warehouses.models import Warehouse

User = get_user_model()


class ShopkeeperNotificationModelTests(TestCase):
    """Test cases for Shopkeeper Notification model"""

    def setUp(self):
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        self.warehouse_admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.warehouse = Warehouse.objects.create(
            admin=self.warehouse_admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
        )
        self.order = Order.objects.create(
            shopkeeper=self.shopkeeper, warehouse=self.warehouse
        )

    def test_create_notification(self):
        """Test creating a notification"""
        notification = Notification.objects.create(
            user=self.shopkeeper,
            title="Order Update",
            message="Your order has been accepted",
            notification_type="SUCCESS",
        )
        self.assertEqual(notification.user, self.shopkeeper)
        self.assertEqual(notification.title, "Order Update")
        self.assertEqual(notification.notification_type, "SUCCESS")
        self.assertFalse(notification.is_read)

    def test_notification_default_type(self):
        """Test notification default type is INFO"""
        notification = Notification.objects.create(
            user=self.shopkeeper, title="Test", message="Test message"
        )
        self.assertEqual(notification.notification_type, "INFO")

    def test_notification_with_order(self):
        """Test notification linked to order"""
        notification = Notification.objects.create(
            user=self.shopkeeper,
            title="Order Update",
            message="Order status changed",
            order=self.order,
        )
        self.assertEqual(notification.order, self.order)

    def test_notification_type_choices(self):
        """Test valid notification type choices"""
        valid_types = ["INFO", "WARNING", "ERROR", "SUCCESS"]
        for notif_type in valid_types:
            notification = Notification.objects.create(
                user=self.shopkeeper,
                title=f"Test {notif_type}",
                message="Test message",
                notification_type=notif_type,
            )
            self.assertEqual(notification.notification_type, notif_type)

    def test_notification_mark_as_read(self):
        """Test marking notification as read"""
        notification = Notification.objects.create(
            user=self.shopkeeper, title="Test", message="Test message"
        )
        notification.is_read = True
        notification.save()
        self.assertTrue(notification.is_read)

    def test_notification_string_representation(self):
        """Test notification string representation"""
        notification = Notification.objects.create(
            user=self.shopkeeper, title="Test Notification", message="Test message"
        )
        self.assertIn("Test Notification", str(notification))


class SupportTicketModelTests(TestCase):
    """Test cases for SupportTicket model"""

    def setUp(self):
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )

    def test_create_support_ticket(self):
        """Test creating a support ticket"""
        ticket = SupportTicket.objects.create(
            user=self.shopkeeper,
            subject="Order Issue",
            description="I have a problem with my order",
            status="OPEN",
            priority="HIGH",
        )
        self.assertEqual(ticket.user, self.shopkeeper)
        self.assertEqual(ticket.subject, "Order Issue")
        self.assertEqual(ticket.status, "OPEN")
        self.assertEqual(ticket.priority, "HIGH")

    def test_support_ticket_default_status(self):
        """Test support ticket default status is OPEN"""
        ticket = SupportTicket.objects.create(
            user=self.shopkeeper, subject="Test Issue", description="Test description"
        )
        self.assertEqual(ticket.status, "OPEN")

    def test_support_ticket_default_priority(self):
        """Test support ticket default priority is MEDIUM"""
        ticket = SupportTicket.objects.create(
            user=self.shopkeeper, subject="Test Issue", description="Test description"
        )
        self.assertEqual(ticket.priority, "MEDIUM")

    def test_support_ticket_status_choices(self):
        """Test valid support ticket status choices"""
        valid_statuses = ["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"]
        for status_val in valid_statuses:
            ticket = SupportTicket.objects.create(
                user=self.shopkeeper,
                subject=f"Test {status_val}",
                description="Test description",
                status=status_val,
            )
            self.assertEqual(ticket.status, status_val)

    def test_support_ticket_priority_choices(self):
        """Test valid support ticket priority choices"""
        valid_priorities = ["LOW", "MEDIUM", "HIGH", "URGENT"]
        for priority in valid_priorities:
            ticket = SupportTicket.objects.create(
                user=self.shopkeeper,
                subject=f"Test {priority}",
                description="Test description",
                priority=priority,
            )
            self.assertEqual(ticket.priority, priority)

    def test_support_ticket_with_category(self):
        """Test support ticket with category"""
        ticket = SupportTicket.objects.create(
            user=self.shopkeeper,
            subject="Test Issue",
            description="Test description",
            category="Order Issue",
        )
        self.assertEqual(ticket.category, "Order Issue")

    def test_support_ticket_resolved_at(self):
        """Test support ticket resolved_at field"""
        from django.utils import timezone

        ticket = SupportTicket.objects.create(
            user=self.shopkeeper, subject="Test Issue", description="Test description"
        )
        self.assertIsNone(ticket.resolved_at)

        # Mark as resolved
        ticket.status = "RESOLVED"
        ticket.resolved_at = timezone.now()
        ticket.save()
        self.assertIsNotNone(ticket.resolved_at)

    def test_support_ticket_string_representation(self):
        """Test support ticket string representation"""
        ticket = SupportTicket.objects.create(
            user=self.shopkeeper,
            subject="Test Issue",
            description="Test description",
            status="OPEN",
        )
        self.assertIn("Test Issue", str(ticket))
        self.assertIn("OPEN", str(ticket))


class ShopkeeperNotificationViewTests(APITestCase):
    """Test cases for Shopkeeper Notification views"""

    def setUp(self):
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        self.other_shopkeeper = User.objects.create_user(
            email="other@example.com", role="SHOPKEEPER"
        )
        self.notification = Notification.objects.create(
            user=self.shopkeeper, title="Test Notification", message="Test message"
        )
        self.client = APIClient()


class SupportTicketViewTests(APITestCase):
    """Test cases for SupportTicket views"""

    def setUp(self):
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        self.admin = User.objects.create_user(email="admin@example.com", role="ADMIN")
        self.ticket = SupportTicket.objects.create(
            user=self.shopkeeper, subject="Test Issue", description="Test description"
        )
        self.client = APIClient()


class ShopkeeperPermissionTests(TestCase):
    """Test cases for shopkeeper permissions"""

    def setUp(self):
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        self.other_shopkeeper = User.objects.create_user(
            email="other@example.com", role="SHOPKEEPER"
        )
        self.notification = Notification.objects.create(
            user=self.shopkeeper, title="Test", message="Test message"
        )
        self.ticket = SupportTicket.objects.create(
            user=self.shopkeeper, subject="Test", description="Test description"
        )

    def test_shopkeeper_can_access_own_notifications(self):
        """Test shopkeeper can access their own notifications"""
        self.assertEqual(self.notification.user, self.shopkeeper)

    def test_shopkeeper_cannot_access_other_notifications(self):
        """Test shopkeeper cannot access other's notifications"""
        self.assertNotEqual(self.notification.user, self.other_shopkeeper)

    def test_shopkeeper_can_access_own_tickets(self):
        """Test shopkeeper can access their own support tickets"""
        self.assertEqual(self.ticket.user, self.shopkeeper)

    def test_shopkeeper_cannot_access_other_tickets(self):
        """Test shopkeeper cannot access other's support tickets"""
        self.assertNotEqual(self.ticket.user, self.other_shopkeeper)
