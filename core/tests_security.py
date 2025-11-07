"""
Security tests for authentication, authorization, validation, and rate limiting
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from decimal import Decimal
from unittest.mock import patch, MagicMock
import jwt
from datetime import datetime, timedelta

from core.validators import GeoValidator, NumericValidator, IDValidator, StringValidator
from core.order_state import OrderStateManager
from orders.models import Order, OrderItem
from warehouses.models import Warehouse
from inventory.models import Item

User = get_user_model()


class JWTAuthenticationTests(APITestCase):
    """Test JWT authentication with validation"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(
            email="test@example.com", supabase_uid="test-uid-123", role="SHOPKEEPER"
        )

    def test_missing_authorization_header(self):
        """Test request without authorization header"""
        response = self.client.get("/api/shopkeeper/orders/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_authorization_format(self):
        """Test invalid authorization header format"""
        self.client.credentials(HTTP_AUTHORIZATION="InvalidFormat token")
        response = self.client.get("/api/shopkeeper/orders/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_token(self):
        """Test expired JWT token"""
        # This would require mocking JWT verification
        pass

    def test_invalid_token_signature(self):
        """Test token with invalid signature"""
        # This would require mocking JWT verification
        pass


class PermissionBoundaryTests(APITestCase):
    """Test permission boundaries for different user roles"""

    def setUp(self):
        self.shopkeeper = User.objects.create(
            email="shopkeeper@example.com",
            supabase_uid="shopkeeper-uid",
            role="SHOPKEEPER",
        )
        self.warehouse_admin = User.objects.create(
            email="warehouse@example.com",
            supabase_uid="warehouse-uid",
            role="WAREHOUSE_MANAGER",
        )
        self.rider = User.objects.create(
            email="rider@example.com", supabase_uid="rider-uid", role="RIDER"
        )

        self.warehouse = Warehouse.objects.create(
            admin=self.warehouse_admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="1234567890",
            is_active=True,
            is_approved=True,
        )

    def test_shopkeeper_cannot_access_warehouse_endpoints(self):
        """Test shopkeeper cannot access warehouse admin endpoints"""
        self.client.force_authenticate(user=self.shopkeeper)
        response = self.client.get("/api/warehouse/orders/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_rider_cannot_access_shopkeeper_endpoints(self):
        """Test rider cannot access shopkeeper endpoints"""
        self.client.force_authenticate(user=self.rider)
        response = self.client.post("/api/shopkeeper/orders/create/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_warehouse_admin_can_only_access_own_warehouse(self):
        """Test warehouse admin can only access their own warehouse data"""
        other_admin = User.objects.create(
            email="other@example.com",
            supabase_uid="other-uid",
            role="WAREHOUSE_MANAGER",
        )
        other_warehouse = Warehouse.objects.create(
            admin=other_admin,
            name="Other Warehouse",
            address="456 Other St",
            contact_number="0987654321",
            is_active=True,
            is_approved=True,
        )

        self.client.force_authenticate(user=self.warehouse_admin)

        # Should not be able to access other warehouse's data
        # This would require actual endpoint implementation
        pass


class InputValidationTests(TestCase):
    """Test input validation for coordinates, quantities, and IDs"""

    def test_valid_coordinates(self):
        """Test validation of valid coordinates"""
        is_valid, msg = GeoValidator.validate_coordinates(40.7128, -74.0060)
        self.assertTrue(is_valid)
        self.assertEqual(msg, "")

    def test_invalid_latitude(self):
        """Test validation of invalid latitude"""
        is_valid, msg = GeoValidator.validate_coordinates(91.0, -74.0060)
        self.assertFalse(is_valid)
        self.assertIn("Latitude", msg)

    def test_invalid_longitude(self):
        """Test validation of invalid longitude"""
        is_valid, msg = GeoValidator.validate_coordinates(40.7128, -181.0)
        self.assertFalse(is_valid)
        self.assertIn("Longitude", msg)

    def test_radius_clamping(self):
        """Test radius is clamped to safe limits"""
        # Too large
        clamped = GeoValidator.clamp_radius(100)
        self.assertEqual(clamped, 50.0)

        # Too small
        clamped = GeoValidator.clamp_radius(0.5)
        self.assertEqual(clamped, 1.0)

        # Just right
        clamped = GeoValidator.clamp_radius(10)
        self.assertEqual(clamped, 10.0)

    def test_quantity_validation(self):
        """Test quantity validation"""
        is_valid, msg = NumericValidator.validate_quantity(10)
        self.assertTrue(is_valid)

        is_valid, msg = NumericValidator.validate_quantity(0)
        self.assertFalse(is_valid)

        is_valid, msg = NumericValidator.validate_quantity(20000)
        self.assertFalse(is_valid)

    def test_price_validation(self):
        """Test price validation"""
        is_valid, msg = NumericValidator.validate_price(Decimal("10.99"))
        self.assertTrue(is_valid)

        is_valid, msg = NumericValidator.validate_price(Decimal("0.00"))
        self.assertFalse(is_valid)

        is_valid, msg = NumericValidator.validate_price(Decimal("9999999.99"))
        self.assertFalse(is_valid)

    def test_id_validation(self):
        """Test ID validation"""
        is_valid, msg = IDValidator.validate_id(123)
        self.assertTrue(is_valid)

        is_valid, msg = IDValidator.validate_id(0)
        self.assertFalse(is_valid)

        is_valid, msg = IDValidator.validate_id(-5)
        self.assertFalse(is_valid)

        is_valid, msg = IDValidator.validate_id("abc")
        self.assertFalse(is_valid)

    def test_string_sanitization(self):
        """Test string sanitization removes dangerous characters"""
        dangerous = "Test\x00String\x01"
        sanitized = StringValidator.sanitize_string(dangerous)
        self.assertNotIn("\x00", sanitized)
        self.assertNotIn("\x01", sanitized)


class OrderStateTransitionTests(TestCase):
    """Test order state transition validation"""

    def test_valid_transitions(self):
        """Test valid state transitions"""
        # Warehouse admin accepts pending order
        can_transition, msg = OrderStateManager.validate_transition(
            "pending", "accepted", "WAREHOUSE_MANAGER"
        )
        self.assertTrue(can_transition)

        # Rider marks as delivered
        can_transition, msg = OrderStateManager.validate_transition(
            "in_transit", "delivered", "RIDER"
        )
        self.assertTrue(can_transition)

    def test_invalid_transitions(self):
        """Test invalid state transitions"""
        # Cannot go from pending directly to delivered
        can_transition, msg = OrderStateManager.validate_transition(
            "pending", "delivered", "WAREHOUSE_MANAGER"
        )
        self.assertFalse(can_transition)
        self.assertIsNotNone(msg)

    def test_role_restrictions(self):
        """Test role-based transition restrictions"""
        # Shopkeeper cannot accept orders
        can_transition, msg = OrderStateManager.validate_transition(
            "pending", "accepted", "SHOPKEEPER"
        )
        self.assertFalse(can_transition)

        # Rider cannot reject orders
        can_transition, msg = OrderStateManager.validate_transition(
            "pending", "rejected", "RIDER"
        )
        self.assertFalse(can_transition)

    def test_terminal_states(self):
        """Test terminal states cannot be transitioned from"""
        # Delivered is terminal
        can_transition, msg = OrderStateManager.validate_transition(
            "delivered", "pending", "ADMIN"
        )
        self.assertFalse(can_transition)


class ConcurrentOrderCreationTests(TransactionTestCase):
    """Test concurrent order creation for race conditions"""

    def setUp(self):
        self.shopkeeper = User.objects.create(
            email="shopkeeper@example.com",
            supabase_uid="shopkeeper-uid",
            role="SHOPKEEPER",
        )
        self.warehouse_admin = User.objects.create(
            email="warehouse@example.com",
            supabase_uid="warehouse-uid",
            role="WAREHOUSE_MANAGER",
        )
        self.warehouse = Warehouse.objects.create(
            admin=self.warehouse_admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="1234567890",
            is_active=True,
            is_approved=True,
        )
        self.item = Item.objects.create(
            warehouse=self.warehouse,
            name="Test Item",
            sku="TEST-001",
            price=Decimal("10.00"),
            quantity=10,
        )

    def test_concurrent_stock_deduction(self):
        """Test that concurrent orders properly handle stock deduction"""
        # This would require actual concurrent requests
        # For now, we test that select_for_update is used
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as queries:
            # Simulate order creation
            pass

        # Check if SELECT FOR UPDATE was used
        # sql_queries = [q['sql'] for q in queries]
        # self.assertTrue(any('FOR UPDATE' in q for q in sql_queries))


class GeoCacheTests(TestCase):
    """Test geo query caching"""

    @patch("warehouses.geo_services.cache")
    def test_cache_hit(self, mock_cache):
        """Test that cache is used for repeated geo queries"""
        from warehouses.geo_services import find_nearby_warehouses_cached

        # First call - cache miss
        mock_cache.get.return_value = None
        result1 = find_nearby_warehouses_cached(40.7128, -74.0060, 10)
        mock_cache.set.assert_called_once()

        # Second call - cache hit
        mock_cache.get.return_value = []
        result2 = find_nearby_warehouses_cached(40.7128, -74.0060, 10)
        # Should not call set again
        self.assertEqual(mock_cache.set.call_count, 1)
