# orders/tests.py
from django.contrib.gis.geos import Point
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from accounts.models import User
from warehouses.models import Warehouse
from inventory.models import Item
from orders.models import Order, OrderItem


class OrderCreationTestCase(APITestCase):
    """Test cases for order creation and flow"""

    def setUp(self):
        """Set up test data"""
        # Create warehouse admin
        self.warehouse_admin = User.objects.create(
            email="warehouse@test.com",
            phone_number="+1234567890",
            role="WAREHOUSE_MANAGER",
            is_active=True,
        )

        # Create shopkeeper
        self.shopkeeper = User.objects.create(
            email="shopkeeper@test.com",
            phone_number="+0987654321",
            role="SHOPKEEPER",
            is_active=True,
        )

        # Create another shopkeeper
        self.shopkeeper2 = User.objects.create(
            email="shopkeeper2@test.com",
            phone_number="+1122334455",
            role="SHOPKEEPER",
            is_active=True,
        )

        # Create warehouse
        self.warehouse = Warehouse.objects.create(
            admin=self.warehouse_admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1111111111",
            is_active=True,
            is_approved=True,
            location=Point(77.5946, 12.9716),  # Bangalore coordinates
        )

        # Create inactive warehouse
        self.inactive_warehouse = Warehouse.objects.create(
            admin=self.warehouse_admin,
            name="Inactive Warehouse",
            address="456 Test Ave",
            contact_number="+2222222222",
            is_active=False,
            is_approved=True,
            location=Point(77.6000, 12.9800),
        )

        # Create items
        self.item1 = Item.objects.create(
            warehouse=self.warehouse,
            name="Product A",
            description="Test product A",
            sku="SKU-001",
            price=Decimal("100.00"),
            quantity=50,
        )

        self.item2 = Item.objects.create(
            warehouse=self.warehouse,
            name="Product B",
            description="Test product B",
            sku="SKU-002",
            price=Decimal("200.00"),
            quantity=30,
        )

        self.item3 = Item.objects.create(
            warehouse=self.warehouse,
            name="Product C - Low Stock",
            description="Test product C",
            sku="SKU-003",
            price=Decimal("150.00"),
            quantity=5,
        )

        # Set up API client
        self.client = APIClient()

    def test_order_creation_success(self):
        """Test successful order creation"""
        self.client.force_authenticate(user=self.shopkeeper)

        data = {
            "warehouse_id": self.warehouse.id,
            "items": [
                {"item_id": self.item1.id, "quantity": 10},
                {"item_id": self.item2.id, "quantity": 5},
            ],
            "notes": "Test order",
        }

        response = self.client.post(
            "/api/orders/shopkeeper/orders/create/", data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["status"], "pending")
        self.assertEqual(response.data["total_amount"], "2000.00")  # 10*100 + 5*200
        self.assertEqual(len(response.data["order_items"]), 2)

        # Verify stock was deducted
        self.item1.refresh_from_db()
        self.item2.refresh_from_db()
        self.assertEqual(self.item1.quantity, 40)  # 50 - 10
        self.assertEqual(self.item2.quantity, 25)  # 30 - 5

        # Verify order exists
        order = Order.objects.get(id=response.data["id"])
        self.assertEqual(order.shopkeeper, self.shopkeeper)
        self.assertEqual(order.warehouse, self.warehouse)

    def test_order_creation_inactive_warehouse(self):
        """Test order creation with inactive warehouse fails"""
        self.client.force_authenticate(user=self.shopkeeper)

        data = {
            "warehouse_id": self.inactive_warehouse.id,
            "items": [{"item_id": self.item1.id, "quantity": 5}],
        }

        response = self.client.post(
            "/api/orders/shopkeeper/orders/create/", data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("warehouse_id", response.data)

    def test_order_creation_insufficient_stock(self):
        """Test order creation with insufficient stock fails"""
        self.client.force_authenticate(user=self.shopkeeper)

        data = {
            "warehouse_id": self.warehouse.id,
            "items": [
                {"item_id": self.item3.id, "quantity": 10}  # Only 5 available
            ],
        }

        response = self.client.post(
            "/api/orders/shopkeeper/orders/create/", data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("items", response.data)

        # Verify stock was not deducted
        self.item3.refresh_from_db()
        self.assertEqual(self.item3.quantity, 5)

    def test_order_creation_duplicate_pending_order(self):
        """Test that duplicate pending orders are prevented"""
        self.client.force_authenticate(user=self.shopkeeper)

        # Create first order
        data = {
            "warehouse_id": self.warehouse.id,
            "items": [{"item_id": self.item1.id, "quantity": 5}],
        }

        response1 = self.client.post(
            "/api/orders/shopkeeper/orders/create/", data, format="json"
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Try to create second order
        response2 = self.client.post(
            "/api/orders/shopkeeper/orders/create/", data, format="json"
        )
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("warehouse_id", response2.data)

    def test_order_creation_unauthorized(self):
        """Test that non-shopkeepers cannot create orders"""
        self.client.force_authenticate(user=self.warehouse_admin)

        data = {
            "warehouse_id": self.warehouse.id,
            "items": [{"item_id": self.item1.id, "quantity": 5}],
        }

        response = self.client.post(
            "/api/orders/shopkeeper/orders/create/", data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_order_creation_wrong_warehouse_items(self):
        """Test that items from different warehouse cannot be ordered"""
        # Create another warehouse
        other_warehouse = Warehouse.objects.create(
            admin=self.warehouse_admin,
            name="Other Warehouse",
            address="789 Other St",
            contact_number="+3333333333",
            is_active=True,
            is_approved=True,
            location=Point(77.7000, 13.0000),
        )

        self.client.force_authenticate(user=self.shopkeeper)

        data = {
            "warehouse_id": other_warehouse.id,
            "items": [
                {
                    "item_id": self.item1.id,
                    "quantity": 5,
                }  # Item belongs to different warehouse
            ],
        }

        response = self.client.post(
            "/api/orders/shopkeeper/orders/create/", data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("items", response.data)

    def test_warehouse_order_list(self):
        """Test warehouse can see orders"""
        # Create orders
        Order.objects.create(
            shopkeeper=self.shopkeeper,
            warehouse=self.warehouse,
            status="pending",
            total_amount=Decimal("500.00"),
        )
        Order.objects.create(
            shopkeeper=self.shopkeeper2,
            warehouse=self.warehouse,
            status="accepted",
            total_amount=Decimal("300.00"),
        )

        self.client.force_authenticate(user=self.warehouse_admin)

        response = self.client.get("/api/orders/warehouse/orders/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_warehouse_pending_orders(self):
        """Test warehouse can filter pending orders"""
        # Create orders with different statuses
        Order.objects.create(
            shopkeeper=self.shopkeeper,
            warehouse=self.warehouse,
            status="pending",
            total_amount=Decimal("500.00"),
        )
        Order.objects.create(
            shopkeeper=self.shopkeeper2,
            warehouse=self.warehouse,
            status="accepted",
            total_amount=Decimal("300.00"),
        )

        self.client.force_authenticate(user=self.warehouse_admin)

        response = self.client.get("/api/orders/warehouse/orders/pending/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["status"], "pending")

    def test_order_accept(self):
        """Test warehouse can accept pending order"""
        order = Order.objects.create(
            shopkeeper=self.shopkeeper,
            warehouse=self.warehouse,
            status="pending",
            total_amount=Decimal("500.00"),
        )

        self.client.force_authenticate(user=self.warehouse_admin)

        response = self.client.post(f"/api/orders/warehouse/orders/{order.id}/accept/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "accepted")

        order.refresh_from_db()
        self.assertEqual(order.status, "accepted")

    def test_order_reject(self):
        """Test warehouse can reject pending order with reason"""
        order = Order.objects.create(
            shopkeeper=self.shopkeeper,
            warehouse=self.warehouse,
            status="pending",
            total_amount=Decimal("500.00"),
        )

        self.client.force_authenticate(user=self.warehouse_admin)

        response = self.client.post(
            f"/api/orders/warehouse/orders/{order.id}/reject/",
            {"rejection_reason": "Out of stock"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "rejected")
        self.assertEqual(response.data["rejection_reason"], "Out of stock")

        order.refresh_from_db()
        self.assertEqual(order.status, "rejected")
        self.assertEqual(order.rejection_reason, "Out of stock")

    def test_shopkeeper_order_list(self):
        """Test shopkeeper can see their orders"""
        # Create orders for different shopkeepers
        Order.objects.create(
            shopkeeper=self.shopkeeper,
            warehouse=self.warehouse,
            status="pending",
            total_amount=Decimal("500.00"),
        )
        Order.objects.create(
            shopkeeper=self.shopkeeper2,
            warehouse=self.warehouse,
            status="pending",
            total_amount=Decimal("300.00"),
        )

        self.client.force_authenticate(user=self.shopkeeper)

        response = self.client.get("/api/orders/shopkeeper/orders/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only shopkeeper's own order

    def test_order_detail_with_items(self):
        """Test order detail includes order items"""
        order = Order.objects.create(
            shopkeeper=self.shopkeeper,
            warehouse=self.warehouse,
            status="pending",
            total_amount=Decimal("500.00"),
        )

        OrderItem.objects.create(
            order=order, item=self.item1, quantity=5, price=self.item1.price
        )

        self.client.force_authenticate(user=self.shopkeeper)

        response = self.client.get(f"/api/orders/shopkeeper/orders/{order.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["order_items"]), 1)
        self.assertEqual(response.data["order_items"][0]["quantity"], 5)
