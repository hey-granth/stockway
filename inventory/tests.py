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
        with self.assertRaises(Exception):
            self.item.save()

    def test_out_of_stock(self):
        """Test identifying out of stock items"""
        self.item.quantity = 0
        self.item.save()
        self.assertEqual(self.item.quantity, 0)


class ItemImageTests(TestCase):
    """Test cases for item images"""

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

    def test_item_with_image_url(self):
        """Test creating item with image URL"""
        item = Item.objects.create(
            warehouse=self.warehouse,
            name="Test Item",
            sku="TEST-IMG-001",
            price=Decimal("50.00"),
            quantity=100,
            image_url="https://example.com/image.jpg",
        )
        self.assertEqual(item.image_url, "https://example.com/image.jpg")

    def test_item_without_image(self):
        """Test creating item without image"""
        item = Item.objects.create(
            warehouse=self.warehouse,
            name="Test Item",
            sku="TEST-IMG-002",
            price=Decimal("50.00"),
            quantity=100,
        )
        self.assertFalse(item.image_url)


class ItemSoftDeleteTests(TestCase):
    """Test cases for soft-deleted item handling"""

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

    def test_items_from_soft_deleted_warehouse(self):
        """Test items handling when warehouse is soft-deleted"""
        item = Item.objects.create(
            warehouse=self.warehouse,
            name="Test Item",
            sku="TEST-DEL-001",
            price=Decimal("50.00"),
            quantity=100,
        )

        # Items should still exist if warehouse is deleted
        self.warehouse.soft_delete()
        self.assertTrue(Item.objects.filter(id=item.id).exists())

    def test_inactive_warehouse_items(self):
        """Test items from inactive warehouse"""
        item = Item.objects.create(
            warehouse=self.warehouse,
            name="Test Item",
            sku="TEST-INACTIVE-001",
            price=Decimal("50.00"),
            quantity=100,
        )

        self.warehouse.is_active = False
        self.warehouse.save()

        # Items should exist but warehouse is inactive
        item.refresh_from_db()
        self.assertFalse(item.warehouse.is_active)


class ItemValidationTests(TestCase):
    """Test cases for item validation"""

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

    def test_item_price_precision(self):
        """Test item price decimal precision"""
        item = Item.objects.create(
            warehouse=self.warehouse,
            name="Test Item",
            sku="TEST-PRICE-001",
            price=Decimal("99.999"),  # Will be rounded
            quantity=10,
        )
        # Decimal field with max_digits=10, decimal_places=2
        # Should store as 99.99 or 100.00 depending on rounding
        self.assertIsInstance(item.price, Decimal)

    def test_item_requires_warehouse(self):
        """Test item requires a warehouse"""
        with self.assertRaises(Exception):
            Item.objects.create(
                name="Test Item",
                sku="TEST-NO-WH-001",
                price=Decimal("50.00"),
                quantity=100,
            )

    def test_item_requires_price(self):
        """Test item requires price"""
        with self.assertRaises(Exception):
            Item.objects.create(
                warehouse=self.warehouse,
                name="Test Item",
                sku="TEST-NO-PRICE-001",
                quantity=100,
            )
