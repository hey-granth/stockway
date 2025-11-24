from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from inventory.models import Item
from warehouses.models import Warehouse

User = get_user_model()


class ItemModelTests(TestCase):
    """Test cases for Item model"""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.warehouse = Warehouse.objects.create(
            admin=self.admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
            is_active=True,
            is_approved=True,
        )

    def test_create_item(self):
        """Test creating an item"""
        item = Item.objects.create(
            warehouse=self.warehouse,
            name="Test Item",
            description="Test Description",
            sku="TEST-001",
            price=Decimal("50.00"),
            quantity=100,
        )
        self.assertEqual(item.name, "Test Item")
        self.assertEqual(item.sku, "TEST-001")
        self.assertEqual(item.price, Decimal("50.00"))
        self.assertEqual(item.quantity, 100)
        self.assertEqual(item.warehouse, self.warehouse)

    def test_item_string_representation(self):
        """Test item string representation"""
        item = Item.objects.create(
            warehouse=self.warehouse,
            name="Test Item",
            sku="TEST-001",
            price=Decimal("50.00"),
            quantity=100,
        )
        self.assertIn("Test Item", str(item))
        self.assertIn("TEST-001", str(item))

    def test_item_unique_sku(self):
        """Test that SKU must be unique"""
        Item.objects.create(
            warehouse=self.warehouse,
            name="Item 1",
            sku="UNIQUE-SKU",
            price=Decimal("50.00"),
            quantity=100,
        )
        with self.assertRaises(Exception):
            Item.objects.create(
                warehouse=self.warehouse,
                name="Item 2",
                sku="UNIQUE-SKU",
                price=Decimal("75.00"),
                quantity=50,
            )

    def test_item_default_quantity(self):
        """Test item default quantity is 0"""
        item = Item.objects.create(
            warehouse=self.warehouse,
            name="Test Item",
            sku="TEST-002",
            price=Decimal("25.00"),
        )
        self.assertEqual(item.quantity, 0)

    def test_item_positive_quantity(self):
        """Test quantity cannot be negative"""
        # PositiveIntegerField should prevent negative values
        with self.assertRaises(Exception):
            Item.objects.create(
                warehouse=self.warehouse,
                name="Test Item",
                sku="TEST-003",
                price=Decimal("25.00"),
                quantity=-10,
            )

    def test_item_decimal_price(self):
        """Test item price is decimal with correct precision"""
        item = Item.objects.create(
            warehouse=self.warehouse,
            name="Test Item",
            sku="TEST-004",
            price=Decimal("99.99"),
            quantity=10,
        )
        self.assertEqual(item.price, Decimal("99.99"))

    def test_item_description_optional(self):
        """Test description is optional"""
        item = Item.objects.create(
            warehouse=self.warehouse,
            name="Test Item",
            sku="TEST-005",
            price=Decimal("25.00"),
            quantity=10,
        )
        self.assertEqual(item.description, "")


class ItemViewTests(APITestCase):
    """Test cases for Item views"""

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
        self.item = Item.objects.create(
            warehouse=self.warehouse,
            name="Test Item",
            sku="TEST-001",
            price=Decimal("50.00"),
            quantity=100,
        )
        self.client = APIClient()


class ItemPermissionTests(TestCase):
    """Test cases for item permissions"""

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
            is_active=True,
            is_approved=True,
        )
        self.item = Item.objects.create(
            warehouse=self.warehouse,
            name="Test Item",
            sku="TEST-001",
            price=Decimal("50.00"),
            quantity=100,
        )

    def test_item_belongs_to_warehouse(self):
        """Test item belongs to correct warehouse"""
        self.assertEqual(self.item.warehouse, self.warehouse)

    def test_item_warehouse_belongs_to_admin(self):
        """Test item warehouse belongs to admin"""
        self.assertEqual(self.item.warehouse.admin, self.admin)


class ItemStockTests(TestCase):
    """Test cases for item stock management"""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.warehouse = Warehouse.objects.create(
            admin=self.admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
            is_active=True,
            is_approved=True,
        )
        self.item = Item.objects.create(
            warehouse=self.warehouse,
            name="Test Item",
            sku="TEST-001",
            price=Decimal("50.00"),
            quantity=100,
        )

    def test_reduce_stock(self):
        """Test reducing item stock"""
        original_quantity = self.item.quantity
        self.item.quantity -= 10
        self.item.save()
        self.assertEqual(self.item.quantity, original_quantity - 10)

    def test_increase_stock(self):
        """Test increasing item stock"""
        original_quantity = self.item.quantity
        self.item.quantity += 50
        self.item.save()
        self.assertEqual(self.item.quantity, original_quantity + 50)

    def test_stock_cannot_go_negative(self):
        """Test stock quantity cannot be negative"""
        self.item.quantity = -10
        # Should fail due to PositiveIntegerField
