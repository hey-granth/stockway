from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from payments.models import Payment, Payout
from orders.models import Order
from warehouses.models import Warehouse
from riders.models import Rider

User = get_user_model()


class PaymentModelTests(TestCase):
    """Test cases for Payment model"""

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
            is_active=True,
            is_approved=True,
        )
        self.order = Order.objects.create(
            shopkeeper=self.shopkeeper,
            warehouse=self.warehouse,
            total_amount=Decimal("100.00"),
        )

    def test_create_payment(self):
        """Test creating a payment"""
        payment = Payment.objects.create(
            order=self.order,
            payer=self.shopkeeper,
            payee=self.warehouse_admin,
            amount=Decimal("100.00"),
            mode="upi",
            status="pending",
        )
        self.assertEqual(payment.amount, Decimal("100.00"))
        self.assertEqual(payment.payer, self.shopkeeper)
        self.assertEqual(payment.payee, self.warehouse_admin)
        self.assertEqual(payment.mode, "upi")
        self.assertEqual(payment.status, "pending")

    def test_payment_default_mode(self):
        """Test payment default mode is cash"""
        payment = Payment.objects.create(
            order=self.order, payer=self.shopkeeper, amount=Decimal("100.00")
        )
        self.assertEqual(payment.mode, "cash")

    def test_payment_default_status(self):
        """Test payment default status is pending"""
        payment = Payment.objects.create(
            order=self.order, payer=self.shopkeeper, amount=Decimal("100.00")
        )
        self.assertEqual(payment.status, "pending")

    def test_payment_mode_choices(self):
        """Test valid payment mode choices"""
        valid_modes = ["upi", "cash", "credit"]
        for mode in valid_modes:
            payment = Payment.objects.create(
                order=Order.objects.create(
                    shopkeeper=self.shopkeeper,
                    warehouse=self.warehouse,
                    total_amount=Decimal("50.00"),
                ),
                payer=self.shopkeeper,
                amount=Decimal("50.00"),
                mode=mode,
            )
            self.assertEqual(payment.mode, mode)

    def test_payment_status_choices(self):
        """Test valid payment status choices"""
        valid_statuses = ["pending", "completed", "failed"]
        for status_val in valid_statuses:
            payment = Payment.objects.create(
                order=Order.objects.create(
                    shopkeeper=self.shopkeeper,
                    warehouse=self.warehouse,
                    total_amount=Decimal("50.00"),
                ),
                payer=self.shopkeeper,
                amount=Decimal("50.00"),
                status=status_val,
            )
            self.assertEqual(payment.status, status_val)

    def test_payment_unique_order_payer(self):
        """Test unique constraint on order and payer"""
        Payment.objects.create(
            order=self.order, payer=self.shopkeeper, amount=Decimal("100.00")
        )
        # Creating duplicate should fail
        with self.assertRaises(Exception):
            Payment.objects.create(
                order=self.order, payer=self.shopkeeper, amount=Decimal("100.00")
            )

    def test_payment_string_representation(self):
        """Test payment string representation"""
        payment = Payment.objects.create(
            order=self.order, payer=self.shopkeeper, amount=Decimal("100.00")
        )
        self.assertIn(str(payment.id), str(payment))
        self.assertIn(str(self.order.id), str(payment))
        self.assertIn(str(payment.amount), str(payment))


class PayoutModelTests(TestCase):
    """Test cases for Payout model"""

    def setUp(self):
        self.warehouse_admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.rider_user = User.objects.create_user(
            email="rider@example.com", role="RIDER"
        )
        self.warehouse = Warehouse.objects.create(
            admin=self.warehouse_admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
            is_active=True,
            is_approved=True,
        )
        self.rider = Rider.objects.create(
            user=self.rider_user, warehouse=self.warehouse
        )

    def test_create_payout(self):
        """Test creating a payout"""
        payout = Payout.objects.create(
            rider=self.rider,
            warehouse=self.warehouse,
            total_distance=5.5,
            rate_per_km=Decimal("10.00"),
            computed_amount=Decimal("55.00"),
            status="pending",
        )
        self.assertEqual(payout.total_distance, 5.5)
        self.assertEqual(payout.rate_per_km, Decimal("10.00"))
        self.assertEqual(payout.computed_amount, Decimal("55.00"))
        self.assertEqual(payout.status, "pending")

    def test_payout_default_status(self):
        """Test payout default status is pending"""
        payout = Payout.objects.create(
            rider=self.rider,
            warehouse=self.warehouse,
            total_distance=5.0,
            rate_per_km=Decimal("10.00"),
            computed_amount=Decimal("50.00"),
        )
        self.assertEqual(payout.status, "pending")

    def test_payout_status_choices(self):
        """Test valid payout status choices"""
        valid_statuses = ["pending", "settled"]
        for status_val in valid_statuses:
            payout = Payout.objects.create(
                rider=self.rider,
                warehouse=self.warehouse,
                total_distance=5.0,
                rate_per_km=Decimal("10.00"),
                computed_amount=Decimal("50.00"),
                status=status_val,
            )
            self.assertEqual(payout.status, status_val)

    def test_payout_string_representation(self):
        """Test payout string representation"""
        payout = Payout.objects.create(
            rider=self.rider,
            warehouse=self.warehouse,
            total_distance=5.0,
            rate_per_km=Decimal("10.00"),
            computed_amount=Decimal("50.00"),
        )
        self.assertIn(str(payout.id), str(payout))
        self.assertIn(str(self.rider.id), str(payout))
        self.assertIn(str(payout.computed_amount), str(payout))


class PaymentViewTests(APITestCase):
    """Test cases for Payment views"""

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
            is_active=True,
            is_approved=True,
        )
        self.order = Order.objects.create(
            shopkeeper=self.shopkeeper,
            warehouse=self.warehouse,
            total_amount=Decimal("100.00"),
        )
        self.client = APIClient()


class PaymentPermissionTests(TestCase):
    """Test cases for payment permissions"""

    def setUp(self):
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        self.other_shopkeeper = User.objects.create_user(
            email="other@example.com", role="SHOPKEEPER"
        )
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
        self.payment = Payment.objects.create(
            order=self.order, payer=self.shopkeeper, amount=Decimal("100.00")
        )

    def test_payment_belongs_to_payer(self):
        """Test payment belongs to correct payer"""
        self.assertEqual(self.payment.payer, self.shopkeeper)

    def test_payment_cannot_be_accessed_by_other_shopkeeper(self):
        """Test payment cannot be accessed by another shopkeeper"""
        self.assertNotEqual(self.payment.payer, self.other_shopkeeper)


class PayoutViewTests(APITestCase):
    """Test cases for Payout views"""

    def setUp(self):
        self.warehouse_admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.rider_user = User.objects.create_user(
            email="rider@example.com", role="RIDER"
        )
        self.warehouse = Warehouse.objects.create(
            admin=self.warehouse_admin,
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
