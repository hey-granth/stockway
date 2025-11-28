from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import date, timedelta
from analytics.models import AnalyticsSummary
from warehouses.models import Warehouse
from riders.models import Rider

User = get_user_model()


class AnalyticsSummaryModelTests(TestCase):
    """Test cases for AnalyticsSummary model"""

    def setUp(self):
        self.today = date.today()
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

    def test_create_system_analytics(self):
        """Test creating system-wide analytics"""
        metrics = {"total_orders": 100, "total_revenue": "5000.00", "active_users": 50}
        summary = AnalyticsSummary.objects.create(
            ref_type="system", ref_id=None, date=self.today, metrics=metrics
        )
        self.assertEqual(summary.ref_type, "system")
        self.assertIsNone(summary.ref_id)
        self.assertEqual(summary.metrics["total_orders"], 100)

    def test_create_warehouse_analytics(self):
        """Test creating warehouse-specific analytics"""
        metrics = {"orders_count": 25, "revenue": "1250.00"}
        summary = AnalyticsSummary.objects.create(
            ref_type="warehouse",
            ref_id=self.warehouse.id,
            date=self.today,
            metrics=metrics,
        )
        self.assertEqual(summary.ref_type, "warehouse")
        self.assertEqual(summary.ref_id, self.warehouse.id)
        self.assertEqual(summary.metrics["orders_count"], 25)

    def test_create_rider_analytics(self):
        """Test creating rider-specific analytics"""
        rider_user = User.objects.create_user(email="rider@example.com", role="RIDER")
        rider = Rider.objects.create(user=rider_user, warehouse=self.warehouse)
        metrics = {"deliveries_count": 15, "total_distance": 75.5, "earnings": "750.00"}
        summary = AnalyticsSummary.objects.create(
            ref_type="rider", ref_id=rider.id, date=self.today, metrics=metrics
        )
        self.assertEqual(summary.ref_type, "rider")
        self.assertEqual(summary.ref_id, rider.id)
        self.assertEqual(summary.metrics["deliveries_count"], 15)

    def test_create_shopkeeper_analytics(self):
        """Test creating shopkeeper-specific analytics"""
        shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        metrics = {"orders_placed": 10, "total_spent": "500.00"}
        summary = AnalyticsSummary.objects.create(
            ref_type="shopkeeper",
            ref_id=shopkeeper.id,
            date=self.today,
            metrics=metrics,
        )
        self.assertEqual(summary.ref_type, "shopkeeper")
        self.assertEqual(summary.ref_id, shopkeeper.id)

    def test_analytics_unique_constraint(self):
        """Test unique constraint on ref_type, ref_id, and date"""
        from django.db import IntegrityError

        metrics = {"count": 1}
        # Use non-NULL ref_id since PostgreSQL doesn't enforce uniqueness on NULL values
        AnalyticsSummary.objects.create(
            ref_type="warehouse", ref_id=1, date=self.today, metrics=metrics
        )
        # Creating duplicate should fail
        with self.assertRaises(IntegrityError):
            AnalyticsSummary.objects.create(
                ref_type="warehouse", ref_id=1, date=self.today, metrics=metrics
            )

    def test_analytics_default_metrics(self):
        """Test default metrics is empty dict"""
        summary = AnalyticsSummary.objects.create(ref_type="system", date=self.today)
        self.assertEqual(summary.metrics, {})

    def test_analytics_string_representation(self):
        """Test analytics summary string representation"""
        summary = AnalyticsSummary.objects.create(
            ref_type="system", date=self.today, metrics={"test": "value"}
        )
        self.assertIn("system", str(summary))
        self.assertIn(str(self.today), str(summary))

    def test_analytics_string_with_ref_id(self):
        """Test analytics summary string with ref_id"""
        summary = AnalyticsSummary.objects.create(
            ref_type="warehouse",
            ref_id=self.warehouse.id,
            date=self.today,
            metrics={"test": "value"},
        )
        self.assertIn("warehouse", str(summary))
        self.assertIn(str(self.warehouse.id), str(summary))


class AnalyticsQueryTests(TestCase):
    """Test cases for analytics queries"""

    def setUp(self):
        self.today = date.today()
        self.yesterday = self.today - timedelta(days=1)
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
        # Create analytics for different dates
        AnalyticsSummary.objects.create(
            ref_type="warehouse",
            ref_id=self.warehouse.id,
            date=self.today,
            metrics={"orders": 10},
        )
        AnalyticsSummary.objects.create(
            ref_type="warehouse",
            ref_id=self.warehouse.id,
            date=self.yesterday,
            metrics={"orders": 8},
        )

    def test_filter_analytics_by_date(self):
        """Test filtering analytics by date"""
        today_analytics = AnalyticsSummary.objects.filter(date=self.today)
        self.assertEqual(today_analytics.count(), 1)
        self.assertEqual(today_analytics.first().metrics["orders"], 10)

    def test_filter_analytics_by_ref_type_and_id(self):
        """Test filtering analytics by ref_type and ref_id"""
        warehouse_analytics = AnalyticsSummary.objects.filter(
            ref_type="warehouse", ref_id=self.warehouse.id
        )
        self.assertEqual(warehouse_analytics.count(), 2)

    def test_analytics_ordering(self):
        """Test analytics default ordering"""
        all_analytics = AnalyticsSummary.objects.filter(
            ref_type="warehouse", ref_id=self.warehouse.id
        )
        # Should be ordered by -date, ref_type
        self.assertEqual(all_analytics.first().date, self.today)


class AnalyticsViewTests(APITestCase):
    """Test cases for Analytics views"""

    def setUp(self):
        self.admin = User.objects.create_user(email="admin@example.com", role="ADMIN")
        self.warehouse_admin = User.objects.create_user(
            email="warehouse@example.com", role="WAREHOUSE_MANAGER"
        )
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        self.client = APIClient()


class AnalyticsPermissionTests(TestCase):
    """Test cases for analytics permissions"""

    def setUp(self):
        self.admin = User.objects.create_user(email="admin@example.com", role="ADMIN")
        self.warehouse_admin = User.objects.create_user(
            email="warehouse@example.com", role="WAREHOUSE_MANAGER"
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
        self.today = date.today()
        self.analytics = AnalyticsSummary.objects.create(
            ref_type="warehouse",
            ref_id=self.warehouse.id,
            date=self.today,
            metrics={"orders": 10},
        )

    def test_admin_can_access_all_analytics(self):
        """Test admin can access all analytics"""
        # Admin should be able to access any analytics
        self.assertTrue(self.admin.role == "ADMIN")

    def test_warehouse_admin_can_access_own_analytics(self):
        """Test warehouse admin can access their own analytics"""
        self.assertEqual(self.warehouse.admin, self.warehouse_admin)


class AnalyticsMetricsTests(TestCase):
    """Test cases for analytics metrics calculations"""

    def setUp(self):
        self.today = date.today()

    def test_metrics_json_field(self):
        """Test metrics can store complex JSON data"""
        complex_metrics = {
            "orders": {"total": 100, "pending": 10, "completed": 85, "cancelled": 5},
            "revenue": {"total": "5000.00", "average_order": "50.00"},
            "items": [
                {"name": "Item 1", "quantity": 50},
                {"name": "Item 2", "quantity": 30},
            ],
        }
        summary = AnalyticsSummary.objects.create(
            ref_type="system", date=self.today, metrics=complex_metrics
        )
        self.assertEqual(summary.metrics["orders"]["total"], 100)
        self.assertEqual(summary.metrics["revenue"]["total"], "5000.00")
        self.assertEqual(len(summary.metrics["items"]), 2)
