from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from decimal import Decimal
from delivery.models import Delivery
from orders.models import Order
from warehouses.models import Warehouse

User = get_user_model()


class DeliveryModelTests(TestCase):
    """Test cases for Delivery model"""

    def setUp(self):
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        self.rider = User.objects.create_user(email="rider@example.com", role="RIDER")
        self.warehouse_admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.warehouse = Warehouse.objects.create(
            admin=self.warehouse_admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
            is_active=True,
            is_approved=True,
        )
        self.order = Order.objects.create(
            shopkeeper=self.shopkeeper,
            warehouse=self.warehouse,
            total_amount=Decimal("100.00"),
        )

    def test_create_delivery(self):
        """Test creating a delivery"""
        delivery = Delivery.objects.create(
            order=self.order,
            rider=self.rider,
            status="assigned",
            delivery_fee=Decimal("20.00"),
        )
        self.assertEqual(delivery.order, self.order)
        self.assertEqual(delivery.rider, self.rider)
        self.assertEqual(delivery.status, "assigned")
        self.assertEqual(delivery.delivery_fee, Decimal("20.00"))

    def test_delivery_default_status(self):
        """Test delivery default status is assigned"""
        delivery = Delivery.objects.create(order=self.order, rider=self.rider)
        self.assertEqual(delivery.status, "assigned")

    def test_delivery_default_fee(self):
        """Test delivery default fee is 0.00"""
        delivery = Delivery.objects.create(order=self.order, rider=self.rider)
        self.assertEqual(delivery.delivery_fee, Decimal("0.00"))

    def test_delivery_status_choices(self):
        """Test valid delivery status choices"""
        valid_statuses = ["assigned", "in_transit", "delivered", "failed"]
        for status_val in valid_statuses:
            delivery = Delivery.objects.create(
                order=Order.objects.create(
                    shopkeeper=self.shopkeeper,
                    warehouse=self.warehouse,
                    total_amount=Decimal("50.00"),
                ),
                rider=self.rider,
                status=status_val,
            )
            self.assertEqual(delivery.status, status_val)

    def test_delivery_one_to_one_with_order(self):
        """Test delivery has one-to-one relationship with order"""
        Delivery.objects.create(order=self.order, rider=self.rider)
        # Creating another delivery for same order should fail
        with self.assertRaises(Exception):
            Delivery.objects.create(order=self.order, rider=self.rider)

    def test_delivery_without_rider(self):
        """Test delivery can be created without rider (nullable)"""
        delivery = Delivery.objects.create(order=self.order, status="assigned")
        self.assertIsNone(delivery.rider)

    def test_delivery_string_representation(self):
        """Test delivery string representation"""
        delivery = Delivery.objects.create(order=self.order, rider=self.rider)
        self.assertIn("Delivery for Order", str(delivery))
        self.assertIn(str(self.order.id), str(delivery))


class DeliveryViewTests(APITestCase):
    """Test cases for Delivery views"""

    def setUp(self):
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        self.rider = User.objects.create_user(email="rider@example.com", role="RIDER")
        self.warehouse_admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.warehouse = Warehouse.objects.create(
            admin=self.warehouse_admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
            is_active=True,
            is_approved=True,
        )
        self.order = Order.objects.create(
            shopkeeper=self.shopkeeper,
            warehouse=self.warehouse,
            total_amount=Decimal("100.00"),
        )
        self.delivery = Delivery.objects.create(order=self.order, rider=self.rider)
        self.client = APIClient()


class DeliveryPermissionTests(TestCase):
    """Test cases for delivery permissions"""

    def setUp(self):
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        self.other_shopkeeper = User.objects.create_user(
            email="other@example.com", role="SHOPKEEPER"
        )
        self.rider = User.objects.create_user(email="rider@example.com", role="RIDER")
        self.warehouse_admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.warehouse = Warehouse.objects.create(
            admin=self.warehouse_admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
            is_active=True,
            is_approved=True,
        )
        self.order = Order.objects.create(
            shopkeeper=self.shopkeeper,
            warehouse=self.warehouse,
            total_amount=Decimal("100.00"),
        )
        self.delivery = Delivery.objects.create(order=self.order, rider=self.rider)

    def test_delivery_belongs_to_order(self):
        """Test delivery belongs to correct order"""
        self.assertEqual(self.delivery.order, self.order)

    def test_delivery_order_belongs_to_shopkeeper(self):
        """Test delivery order belongs to correct shopkeeper"""
        self.assertEqual(self.delivery.order.shopkeeper, self.shopkeeper)

    def test_delivery_assigned_to_rider(self):
        """Test delivery is assigned to correct rider"""
        self.assertEqual(self.delivery.rider, self.rider)


class DeliveryStatusTransitionTests(TestCase):
    """Test cases for delivery status transitions"""

    def setUp(self):
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        self.rider = User.objects.create_user(email="rider@example.com", role="RIDER")
        self.warehouse_admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.warehouse = Warehouse.objects.create(
            admin=self.warehouse_admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
            is_active=True,
            is_approved=True,
        )
        self.order = Order.objects.create(
            shopkeeper=self.shopkeeper,
            warehouse=self.warehouse,
            total_amount=Decimal("100.00"),
        )
        self.delivery = Delivery.objects.create(
            order=self.order, rider=self.rider, status="assigned"
        )

    def test_delivery_transition_to_in_transit(self):
        """Test delivery status transition to in_transit"""
        self.delivery.status = "in_transit"
        self.delivery.save()
        self.assertEqual(self.delivery.status, "in_transit")

    def test_delivery_transition_to_delivered(self):
        """Test delivery status transition to delivered"""
        self.delivery.status = "delivered"
        self.delivery.save()
        self.assertEqual(self.delivery.status, "delivered")

    def test_delivery_transition_to_failed(self):
        """Test delivery status transition to failed"""
        self.delivery.status = "failed"
        self.delivery.save()
        self.assertEqual(self.delivery.status, "failed")


class DeliveryFeeTests(TestCase):
    """Test cases for delivery fee validation"""

    def setUp(self):
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        self.rider = User.objects.create_user(email="rider@example.com", role="RIDER")
        self.warehouse_admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.warehouse = Warehouse.objects.create(
            admin=self.warehouse_admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
            is_active=True,
            is_approved=True,
        )
        self.order = Order.objects.create(
            shopkeeper=self.shopkeeper,
            warehouse=self.warehouse,
            total_amount=Decimal("100.00"),
        )

    def test_delivery_fee_default_zero(self):
        """Test delivery fee defaults to zero"""
        delivery = Delivery.objects.create(order=self.order, rider=self.rider)
        self.assertEqual(delivery.delivery_fee, Decimal("0.00"))

    def test_delivery_fee_positive(self):
        """Test delivery fee can be set to positive amount"""
        delivery = Delivery.objects.create(
            order=self.order, rider=self.rider, delivery_fee=Decimal("25.00")
        )
        self.assertEqual(delivery.delivery_fee, Decimal("25.00"))

    def test_delivery_fee_precision(self):
        """Test delivery fee decimal precision"""
        delivery = Delivery.objects.create(
            order=self.order, rider=self.rider, delivery_fee=Decimal("12.99")
        )
        self.assertEqual(delivery.delivery_fee, Decimal("12.99"))


class DeliveryTimestampTests(TestCase):
    """Test cases for delivery timestamp tracking"""

    def setUp(self):
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        self.rider = User.objects.create_user(email="rider@example.com", role="RIDER")
        self.warehouse_admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.warehouse = Warehouse.objects.create(
            admin=self.warehouse_admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
            is_active=True,
            is_approved=True,
        )
        self.order = Order.objects.create(
            shopkeeper=self.shopkeeper,
            warehouse=self.warehouse,
            total_amount=Decimal("100.00"),
        )

    def test_delivery_created_at_auto_set(self):
        """Test delivery created_at is automatically set"""
        delivery = Delivery.objects.create(order=self.order, rider=self.rider)
        self.assertIsNotNone(delivery.created_at)

    def test_delivery_updated_at_auto_set(self):
        """Test delivery updated_at is automatically set"""
        delivery = Delivery.objects.create(order=self.order, rider=self.rider)
        self.assertIsNotNone(delivery.updated_at)


class DeliveryRiderAssignmentTests(TestCase):
    """Test cases for rider assignment to deliveries"""

    def setUp(self):
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        self.rider1 = User.objects.create_user(email="rider1@example.com", role="RIDER")
        self.rider2 = User.objects.create_user(email="rider2@example.com", role="RIDER")
        self.warehouse_admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.warehouse = Warehouse.objects.create(
            admin=self.warehouse_admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
            is_active=True,
            is_approved=True,
        )
        self.order = Order.objects.create(
            shopkeeper=self.shopkeeper,
            warehouse=self.warehouse,
            total_amount=Decimal("100.00"),
        )

    def test_delivery_can_be_reassigned(self):
        """Test delivery can be reassigned to different rider"""
        delivery = Delivery.objects.create(
            order=self.order, rider=self.rider1, status="assigned"
        )
        self.assertEqual(delivery.rider, self.rider1)

        delivery.rider = self.rider2
        delivery.save()
        self.assertEqual(delivery.rider, self.rider2)

    def test_delivery_without_rider_allowed(self):
        """Test delivery can exist without rider assignment"""
        delivery = Delivery.objects.create(order=self.order, status="assigned")
        self.assertIsNone(delivery.rider)


class DeliveryOrderRelationshipTests(TestCase):
    """Test cases for delivery-order relationship"""

    def setUp(self):
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        self.rider = User.objects.create_user(email="rider@example.com", role="RIDER")
        self.warehouse_admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.warehouse = Warehouse.objects.create(
            admin=self.warehouse_admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
            is_active=True,
            is_approved=True,
        )

    def test_one_delivery_per_order(self):
        """Test one-to-one relationship: one delivery per order"""
        order = Order.objects.create(
            shopkeeper=self.shopkeeper,
            warehouse=self.warehouse,
            total_amount=Decimal("100.00"),
        )
        Delivery.objects.create(order=order, rider=self.rider)

        # Creating another delivery for same order should fail
        with self.assertRaises(Exception):
            Delivery.objects.create(order=order, rider=self.rider)

    def test_delivery_linked_to_order_shopkeeper(self):
        """Test delivery is properly linked to order's shopkeeper"""
        order = Order.objects.create(
            shopkeeper=self.shopkeeper,
            warehouse=self.warehouse,
            total_amount=Decimal("100.00"),
        )
        delivery = Delivery.objects.create(order=order, rider=self.rider)

        self.assertEqual(delivery.order.shopkeeper, self.shopkeeper)

    def test_delivery_linked_to_order_warehouse(self):
        """Test delivery is properly linked to order's warehouse"""
        order = Order.objects.create(
            shopkeeper=self.shopkeeper,
            warehouse=self.warehouse,
            total_amount=Decimal("100.00"),
        )
        delivery = Delivery.objects.create(order=order, rider=self.rider)

        self.assertEqual(delivery.order.warehouse, self.warehouse)
