from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from warehouses.models import Warehouse, WarehouseNotification, RiderPayout
from riders.models import Rider
from orders.models import Order

User = get_user_model()


class WarehouseModelTests(TestCase):
    """Test cases for Warehouse model"""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )

    def test_create_warehouse(self):
        """Test creating a warehouse"""
        warehouse = Warehouse.objects.create(
            admin=self.admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
        )
        self.assertEqual(warehouse.name, "Test Warehouse")
        self.assertEqual(warehouse.admin, self.admin)
        self.assertTrue(warehouse.is_active)
        self.assertFalse(warehouse.is_approved)

    def test_warehouse_with_location(self):
        """Test warehouse with PostGIS location"""
        location = Point(77.5946, 12.9716, srid=4326)
        warehouse = Warehouse.objects.create(
            admin=self.admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
            location=location,
        )
        self.assertIsNotNone(warehouse.location)
        self.assertAlmostEqual(warehouse.latitude, 12.9716, places=4)
        self.assertAlmostEqual(warehouse.longitude, 77.5946, places=4)

    def test_warehouse_set_coordinates(self):
        """Test setting coordinates"""
        warehouse = Warehouse.objects.create(
            admin=self.admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
        )
        warehouse.set_coordinates(12.9716, 77.5946)
        warehouse.save()
        self.assertIsNotNone(warehouse.location)
        self.assertAlmostEqual(warehouse.latitude, 12.9716, places=4)

    def test_warehouse_invalid_latitude(self):
        """Test warehouse with invalid latitude"""
        warehouse = Warehouse(
            admin=self.admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
            location=Point(77.5946, 95.0, srid=4326),  # Invalid latitude
        )
        with self.assertRaises(ValueError):
            warehouse.save()

    def test_warehouse_invalid_longitude(self):
        """Test warehouse with invalid longitude"""
        warehouse = Warehouse(
            admin=self.admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
            location=Point(200.0, 12.9716, srid=4326),  # Invalid longitude
        )
        with self.assertRaises(ValueError):
            warehouse.save()

    def test_warehouse_string_representation(self):
        """Test warehouse string representation"""
        warehouse = Warehouse.objects.create(
            admin=self.admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
        )
        self.assertIn("Test Warehouse", str(warehouse))
        self.assertIn(self.admin.email, str(warehouse))


class WarehouseNotificationModelTests(TestCase):
    """Test cases for WarehouseNotification model"""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.warehouse = Warehouse.objects.create(
            admin=self.admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
        )

    def test_create_warehouse_notification(self):
        """Test creating a warehouse notification"""
        notification = WarehouseNotification.objects.create(
            warehouse=self.warehouse,
            notification_type="order",
            title="New Order",
            message="You have a new order",
        )
        self.assertEqual(notification.notification_type, "order")
        self.assertFalse(notification.is_read)
        self.assertEqual(notification.warehouse, self.warehouse)

    def test_warehouse_notification_with_metadata(self):
        """Test notification with metadata"""
        metadata = {"order_id": 123, "amount": "100.00"}
        notification = WarehouseNotification.objects.create(
            warehouse=self.warehouse,
            notification_type="order",
            title="New Order",
            message="You have a new order",
            metadata=metadata,
        )
        self.assertEqual(notification.metadata["order_id"], 123)

    def test_warehouse_notification_default_metadata(self):
        """Test notification default metadata is empty dict"""
        notification = WarehouseNotification.objects.create(
            warehouse=self.warehouse,
            notification_type="order",
            title="Test",
            message="Test message",
        )
        self.assertEqual(notification.metadata, {})


class RiderPayoutModelTests(TestCase):
    """Test cases for RiderPayout model"""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.rider_user = User.objects.create_user(
            email="rider@example.com", role="RIDER"
        )
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        self.warehouse = Warehouse.objects.create(
            admin=self.admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
            is_active=True,
            is_approved=True,
        )
        self.rider = Rider.objects.create(
            user=self.rider_user, warehouse=self.warehouse
        )
        self.order = Order.objects.create(
            shopkeeper=self.shopkeeper, warehouse=self.warehouse
        )

    def test_create_rider_payout(self):
        """Test creating a rider payout"""
        payout = RiderPayout.objects.create(
            warehouse=self.warehouse,
            rider=self.rider,
            order=self.order,
            base_rate=Decimal("50.00"),
            distance_km=Decimal("5.0"),
            distance_rate=Decimal("10.00"),
        )
        self.assertEqual(payout.status, "pending")
        self.assertEqual(payout.total_amount, Decimal("100.00"))

    def test_payout_total_calculation(self):
        """Test payout total amount calculation"""
        payout = RiderPayout.objects.create(
            warehouse=self.warehouse,
            rider=self.rider,
            order=self.order,
            base_rate=Decimal("30.00"),
            distance_km=Decimal("7.5"),
            distance_rate=Decimal("8.00"),
        )
        # 30.00 + (7.5 * 8.00) = 90.00
        self.assertEqual(payout.total_amount, Decimal("90.00"))

    def test_payout_calculate_total_method(self):
        """Test calculate_total method"""
        payout = RiderPayout(
            warehouse=self.warehouse,
            rider=self.rider,
            order=self.order,
            base_rate=Decimal("40.00"),
            distance_km=Decimal("3.0"),
            distance_rate=Decimal("12.00"),
        )
        total = payout.calculate_total()
        self.assertEqual(total, Decimal("76.00"))


class WarehouseViewTests(APITestCase):
    """Test cases for Warehouse views"""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.other_admin = User.objects.create_user(
            email="other@example.com", role="WAREHOUSE_MANAGER"
        )
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        self.warehouse = Warehouse.objects.create(
            admin=self.admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
            is_active=True,
            is_approved=True,
        )
        self.client = APIClient()


class WarehousePermissionTests(TestCase):
    """Test cases for warehouse permissions"""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.other_admin = User.objects.create_user(
            email="other@example.com", role="WAREHOUSE_MANAGER"
        )
        self.warehouse = Warehouse.objects.create(
            admin=self.admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
        )

    def test_admin_can_access_own_warehouse(self):
        """Test admin can access their own warehouse"""
        self.assertEqual(self.warehouse.admin, self.admin)

    def test_admin_cannot_access_other_warehouse(self):
        """Test admin cannot access other admin's warehouse"""
        self.assertNotEqual(self.warehouse.admin, self.other_admin)
