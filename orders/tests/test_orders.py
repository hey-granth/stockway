from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from orders.models import Order, OrderItem
from warehouses.models import Warehouse
from inventory.models import Item
from delivery.models import Delivery
from django.contrib.gis.geos import Point
from unittest.mock import patch

User = get_user_model()


class OrderModelTests(TestCase):
    """Test cases for Order model"""

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

    def test_create_order(self):
        """Test creating an order"""
        order = Order.objects.create(
            shopkeeper=self.shopkeeper,
            warehouse=self.warehouse,
            status="pending",
            total_amount=Decimal("100.00"),
        )
        self.assertEqual(order.status, "pending")
        self.assertEqual(order.total_amount, Decimal("100.00"))
        self.assertEqual(order.shopkeeper, self.shopkeeper)
        self.assertEqual(order.warehouse, self.warehouse)

    def test_order_default_status(self):
        """Test order default status is pending"""
        order = Order.objects.create(
            shopkeeper=self.shopkeeper, warehouse=self.warehouse
        )
        self.assertEqual(order.status, "pending")

    def test_order_total_amount_non_negative_constraint(self):
        """Test that total_amount cannot be negative"""
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            Order.objects.create(
                shopkeeper=self.shopkeeper,
                warehouse=self.warehouse,
                total_amount=Decimal("-100.00"),
            )

    def test_order_string_representation(self):
        """Test order string representation"""
        order = Order.objects.create(
            shopkeeper=self.shopkeeper, warehouse=self.warehouse
        )
        self.assertIn(f"Order #{order.id}", str(order))

    def test_order_status_choices(self):
        """Test valid order status choices"""
        valid_statuses = [
            "pending",
            "accepted",
            "rejected",
            "assigned",
            "in_transit",
            "delivered",
            "cancelled",
        ]
        for status_val in valid_statuses:
            order = Order.objects.create(
                shopkeeper=self.shopkeeper, warehouse=self.warehouse, status=status_val
            )
            self.assertEqual(order.status, status_val)


class OrderItemModelTests(TestCase):
    """Test cases for OrderItem model"""

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
        self.item = Item.objects.create(
            warehouse=self.warehouse,
            name="Test Item",
            sku="TEST-001",
            price=Decimal("50.00"),
            quantity=100,
        )
        self.order = Order.objects.create(
            shopkeeper=self.shopkeeper, warehouse=self.warehouse
        )

    def test_create_order_item(self):
        """Test creating an order item"""
        order_item = OrderItem.objects.create(
            order=self.order, item=self.item, quantity=5, price=Decimal("50.00")
        )
        self.assertEqual(order_item.quantity, 5)
        self.assertEqual(order_item.price, Decimal("50.00"))
        self.assertEqual(order_item.order, self.order)
        self.assertEqual(order_item.item, self.item)

    def test_order_item_quantity_positive_constraint(self):
        """Test that quantity must be positive"""
        # Creating with quantity 0 should violate constraint
        with self.assertRaises(Exception):
            OrderItem.objects.create(
                order=self.order, item=self.item, quantity=0, price=Decimal("50.00")
            )

    def test_order_item_price_non_negative_constraint(self):
        """Test that price cannot be negative"""
        # Creating with negative price should violate constraint
        with self.assertRaises(Exception):
            OrderItem.objects.create(
                order=self.order, item=self.item, quantity=5, price=Decimal("-50.00")
            )

    def test_order_item_string_representation(self):
        """Test order item string representation"""
        order_item = OrderItem.objects.create(
            order=self.order, item=self.item, quantity=5, price=Decimal("50.00")
        )
        self.assertIn(self.item.name, str(order_item))
        self.assertIn(str(self.order.id), str(order_item))


class OrderCreateViewTests(APITestCase):
    """Test cases for OrderCreateView"""

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
        self.item1 = Item.objects.create(
            warehouse=self.warehouse,
            name="Item 1",
            sku="ITEM-001",
            price=Decimal("50.00"),
            quantity=100,
        )
        self.item2 = Item.objects.create(
            warehouse=self.warehouse,
            name="Item 2",
            sku="ITEM-002",
            price=Decimal("75.00"),
            quantity=50,
        )
        self.client = APIClient()
        self.url = "/api/shopkeeper/orders/create/"

    def test_create_order_success(self):
        """Test successful order creation"""
        self.client.force_authenticate(user=self.shopkeeper)
        data = {
            "warehouse_id": self.warehouse.id,
            "items": [
                {"item_id": self.item1.id, "quantity": 5},
                {"item_id": self.item2.id, "quantity": 3},
            ],
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)

        # Verify order was created
        order = Order.objects.get(id=response.data["id"])
        self.assertEqual(order.shopkeeper, self.shopkeeper)
        self.assertEqual(order.warehouse, self.warehouse)
        self.assertEqual(order.status, "pending")

    def test_create_order_unauthenticated(self):
        """Test creating order without authentication"""
        data = {
            "warehouse_id": self.warehouse.id,
            "items": [{"item_id": self.item1.id, "quantity": 5}],
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_order_wrong_role(self):
        """Test creating order with non-shopkeeper role"""
        self.client.force_authenticate(user=self.warehouse_admin)
        data = {
            "warehouse_id": self.warehouse.id,
            "items": [{"item_id": self.item1.id, "quantity": 5}],
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_order_invalid_warehouse(self):
        """Test creating order with invalid warehouse"""
        self.client.force_authenticate(user=self.shopkeeper)
        data = {
            "warehouse_id": 99999,
            "items": [{"item_id": self.item1.id, "quantity": 5}],
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_inactive_warehouse(self):
        """Test creating order with inactive warehouse"""
        self.warehouse.is_active = False
        self.warehouse.save()

        self.client.force_authenticate(user=self.shopkeeper)
        data = {
            "warehouse_id": self.warehouse.id,
            "items": [{"item_id": self.item1.id, "quantity": 5}],
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_no_items(self):
        """Test creating order with no items"""
        self.client.force_authenticate(user=self.shopkeeper)
        data = {"warehouse_id": self.warehouse.id, "items": []}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_insufficient_stock(self):
        """Test creating order with insufficient stock"""
        self.client.force_authenticate(user=self.shopkeeper)
        data = {
            "warehouse_id": self.warehouse.id,
            "items": [
                {"item_id": self.item1.id, "quantity": 200}
            ],  # More than available
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_duplicate_items(self):
        """Test creating order with duplicate items"""
        self.client.force_authenticate(user=self.shopkeeper)
        data = {
            "warehouse_id": self.warehouse.id,
            "items": [
                {"item_id": self.item1.id, "quantity": 5},
                {"item_id": self.item1.id, "quantity": 3},
            ],
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ShopkeeperOrderListViewTests(APITestCase):
    """Test cases for ShopkeeperOrderListView"""

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
        # Create orders
        self.order1 = Order.objects.create(
            shopkeeper=self.shopkeeper, warehouse=self.warehouse
        )
        self.order2 = Order.objects.create(
            shopkeeper=self.shopkeeper, warehouse=self.warehouse
        )
        self.other_order = Order.objects.create(
            shopkeeper=self.other_shopkeeper, warehouse=self.warehouse
        )
        self.client = APIClient()
        self.url = "/api/shopkeeper/orders/"

    def test_list_orders_authenticated_shopkeeper(self):
        """Test listing orders for authenticated shopkeeper"""
        self.client.force_authenticate(user=self.shopkeeper)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only see own orders
        self.assertEqual(len(response.data), 2)

    def test_list_orders_unauthenticated(self):
        """Test listing orders without authentication"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_orders_wrong_role(self):
        """Test listing orders with wrong role"""
        self.client.force_authenticate(user=self.warehouse_admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_orders_only_own_orders(self):
        """Test that shopkeeper only sees their own orders"""
        self.client.force_authenticate(user=self.shopkeeper)
        response = self.client.get(self.url)
        order_ids = [order["id"] for order in response.data]
        self.assertIn(self.order1.id, order_ids)
        self.assertIn(self.order2.id, order_ids)
        self.assertNotIn(self.other_order.id, order_ids)


class WarehouseOrderListViewTests(APITestCase):
    """Test cases for WarehouseOrderListView"""

    def setUp(self):
        self.warehouse_admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.other_admin = User.objects.create_user(
            email="other_admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        self.warehouse = Warehouse.objects.create(
            admin=self.warehouse_admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
            is_active=True,
            is_approved=True,
        )
        self.other_warehouse = Warehouse.objects.create(
            admin=self.other_admin,
            name="Other Warehouse",
            address="456 Other St",
            contact_number="+0987654321",
            is_active=True,
            is_approved=True,
        )
        # Create orders
        self.order1 = Order.objects.create(
            shopkeeper=self.shopkeeper, warehouse=self.warehouse
        )
        self.other_order = Order.objects.create(
            shopkeeper=self.shopkeeper, warehouse=self.other_warehouse
        )
        self.client = APIClient()
        self.url = "/api/warehouse/orders/"

    def test_list_orders_warehouse_admin(self):
        """Test listing orders for warehouse admin"""
        self.client.force_authenticate(user=self.warehouse_admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only see orders for their warehouse
        self.assertEqual(len(response.data), 1)

    def test_list_orders_filter_by_status(self):
        """Test filtering orders by status"""
        self.order1.status = "accepted"
        self.order1.save()

        self.client.force_authenticate(user=self.warehouse_admin)
        response = self.client.get(f"{self.url}?status=accepted")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class OrderAcceptViewTests(APITestCase):
    """Test cases for OrderAcceptView"""

    def setUp(self):
        self.warehouse_admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
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
            shopkeeper=self.shopkeeper, warehouse=self.warehouse, status="pending"
        )
        self.client = APIClient()
        self.url = f"/api/warehouse/orders/{self.order.id}/accept/"

    @patch("orders.views.OrderStateManager.validate_transition")
    @patch("orders.views.OrderStateManager.log_transition")
    def test_accept_order_success(self, mock_log, mock_validate):
        """Test successful order acceptance"""
        mock_validate.return_value = (True, None)

        self.client.force_authenticate(user=self.warehouse_admin)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify order status changed
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "accepted")

    def test_accept_order_unauthenticated(self):
        """Test accepting order without authentication"""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_accept_order_wrong_role(self):
        """Test accepting order with wrong role"""
        self.client.force_authenticate(user=self.shopkeeper)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("orders.views.OrderStateManager.validate_transition")
    def test_accept_order_invalid_state_transition(self, mock_validate):
        """Test accepting order with invalid state transition"""
        mock_validate.return_value = (False, "Invalid state transition")

        self.client.force_authenticate(user=self.warehouse_admin)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OrderRejectViewTests(APITestCase):
    """Test cases for OrderRejectView"""

    def setUp(self):
        self.warehouse_admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
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
            shopkeeper=self.shopkeeper, warehouse=self.warehouse, status="pending"
        )
        self.client = APIClient()
        self.url = f"/api/warehouse/orders/{self.order.id}/reject/"

    @patch("orders.views.OrderStateManager.validate_transition")
    def test_reject_order_success(self, mock_validate):
        """Test successful order rejection"""
        mock_validate.return_value = (True, None)

        self.client.force_authenticate(user=self.warehouse_admin)
        data = {"rejection_reason": "Out of stock for requested items"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify order status and reason
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "rejected")
        self.assertIsNotNone(self.order.rejection_reason)

    def test_reject_order_missing_reason(self):
        """Test rejecting order without reason"""
        self.client.force_authenticate(user=self.warehouse_admin)
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_order_unauthenticated(self):
        """Test rejecting order without authentication"""
        data = {"rejection_reason": "Test reason"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
