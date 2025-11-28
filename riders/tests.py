from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from riders.models import Rider, RiderNotification
from warehouses.models import Warehouse

User = get_user_model()


class RiderModelTests(TestCase):
    """Test cases for Rider model"""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.rider_user = User.objects.create_user(
            email="rider@example.com", role="RIDER"
        )
        self.warehouse = Warehouse.objects.create(
            admin=self.admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
            is_active=True,
            is_approved=True,
        )

    def test_create_rider(self):
        """Test creating a rider"""
        rider = Rider.objects.create(user=self.rider_user, warehouse=self.warehouse)
        self.assertEqual(rider.user, self.rider_user)
        self.assertEqual(rider.warehouse, self.warehouse)
        self.assertEqual(rider.status, "available")
        self.assertEqual(rider.availability, "available")
        self.assertEqual(rider.total_earnings, Decimal("0.00"))
        self.assertFalse(rider.is_suspended)

    def test_rider_with_location(self):
        """Test rider with location"""
        location = Point(77.5946, 12.9716, srid=4326)
        rider = Rider.objects.create(
            user=self.rider_user, warehouse=self.warehouse, current_location=location
        )
        self.assertIsNotNone(rider.current_location)
        self.assertAlmostEqual(rider.latitude, 12.9716, places=4)
        self.assertAlmostEqual(rider.longitude, 77.5946, places=4)

    def test_rider_set_coordinates(self):
        """Test setting rider coordinates"""
        rider = Rider.objects.create(user=self.rider_user, warehouse=self.warehouse)
        rider.set_coordinates(12.9716, 77.5946)
        rider.save()
        self.assertIsNotNone(rider.current_location)
        self.assertAlmostEqual(rider.latitude, 12.9716, places=4)

    def test_rider_invalid_latitude(self):
        """Test rider with invalid latitude"""
        rider = Rider(
            user=self.rider_user,
            warehouse=self.warehouse,
            current_location=Point(77.5946, 95.0, srid=4326),
        )
        with self.assertRaises(ValueError):
            rider.save()

    def test_rider_invalid_longitude(self):
        """Test rider with invalid longitude"""
        rider = Rider(
            user=self.rider_user,
            warehouse=self.warehouse,
            current_location=Point(200.0, 12.9716, srid=4326),
        )
        with self.assertRaises(ValueError):
            rider.save()

    def test_rider_latitude_property(self):
        """Test rider latitude property"""
        rider = Rider.objects.create(user=self.rider_user, warehouse=self.warehouse)
        self.assertIsNone(rider.latitude)

        rider.set_coordinates(12.9716, 77.5946)
        rider.save()
        rider.refresh_from_db()
        self.assertIsNotNone(rider.latitude)

    def test_rider_longitude_property(self):
        """Test rider longitude property"""
        rider = Rider.objects.create(user=self.rider_user, warehouse=self.warehouse)
        self.assertIsNone(rider.longitude)

        rider.set_coordinates(12.9716, 77.5946)
        rider.save()
        rider.refresh_from_db()
        self.assertIsNotNone(rider.longitude)

    def test_rider_status_choices(self):
        """Test rider status choices"""
        valid_statuses = ["available", "busy", "inactive"]
        for status_val in valid_statuses:
            rider = Rider.objects.create(
                user=User.objects.create_user(
                    email=f"rider_{status_val}@example.com", role="RIDER"
                ),
                warehouse=self.warehouse,
                status=status_val,
            )
            self.assertEqual(rider.status, status_val)

    def test_rider_availability_choices(self):
        """Test rider availability choices"""
        valid_availability = ["available", "off-duty"]
        for avail in valid_availability:
            rider = Rider.objects.create(
                user=User.objects.create_user(
                    email=f"rider_{avail}@example.com", role="RIDER"
                ),
                warehouse=self.warehouse,
                availability=avail,
            )
            self.assertEqual(rider.availability, avail)

    def test_rider_suspension(self):
        """Test rider suspension"""
        rider = Rider.objects.create(
            user=self.rider_user,
            warehouse=self.warehouse,
            is_suspended=True,
            suspension_reason="Violated policy",
        )
        self.assertTrue(rider.is_suspended)
        self.assertIsNotNone(rider.suspension_reason)

    def test_rider_total_earnings_non_negative(self):
        """Test rider total earnings cannot be negative"""
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            Rider.objects.create(
                user=self.rider_user,
                warehouse=self.warehouse,
                total_earnings=Decimal("-10.00"),
            )


class RiderNotificationModelTests(TestCase):
    """Test cases for RiderNotification model"""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.rider_user = User.objects.create_user(
            email="rider@example.com", role="RIDER"
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

    def test_create_rider_notification(self):
        """Test creating a rider notification"""
        notification = RiderNotification.objects.create(
            rider=self.rider, notification_type="order_assigned", title="New Delivery"
        )
        self.assertEqual(notification.notification_type, "order_assigned")
        self.assertEqual(notification.rider, self.rider)

    def test_rider_notification_types(self):
        """Test valid notification types"""
        valid_types = [
            "order_assigned",
            "order_update",
            "payment",
            "general",
            "suspension",
        ]
        for notif_type in valid_types:
            notification = RiderNotification.objects.create(
                rider=self.rider,
                notification_type=notif_type,
                title=f"Test {notif_type}",
            )
            self.assertEqual(notification.notification_type, notif_type)


class RiderViewTests(APITestCase):
    """Test cases for Rider views"""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.rider_user = User.objects.create_user(
            email="rider@example.com", role="RIDER"
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
        self.client = APIClient()


class RiderPermissionTests(TestCase):
    """Test cases for rider permissions"""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.other_admin = User.objects.create_user(
            email="other@example.com", role="WAREHOUSE_MANAGER"
        )
        self.rider_user = User.objects.create_user(
            email="rider@example.com", role="RIDER"
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

    def test_rider_belongs_to_warehouse(self):
        """Test rider belongs to correct warehouse"""
        self.assertEqual(self.rider.warehouse, self.warehouse)

    def test_rider_belongs_to_admin(self):
        """Test rider warehouse belongs to admin"""
        self.assertEqual(self.rider.warehouse.admin, self.admin)


class RiderLocationTests(TestCase):
    """Test cases for rider location updates"""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.rider_user = User.objects.create_user(
            email="rider@example.com", role="RIDER"
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

    def test_update_rider_location(self):
        """Test updating rider location"""
        self.rider.set_coordinates(12.9716, 77.5946)
        self.rider.save()
        self.assertIsNotNone(self.rider.current_location)

    def test_rider_location_validation(self):
        """Test rider location coordinate validation"""
        # Valid coordinates
        self.rider.set_coordinates(12.9716, 77.5946)
        self.rider.save()
        # Should not raise error

    def test_rider_latitude_bounds(self):
        """Test latitude must be within -90 to 90"""
        with self.assertRaises(ValueError):
            self.rider.set_coordinates(95.0, 77.5946)
            self.rider.save()

    def test_rider_longitude_bounds(self):
        """Test longitude must be within -180 to 180"""
        with self.assertRaises(ValueError):
            self.rider.set_coordinates(12.9716, 200.0)
            self.rider.save()
