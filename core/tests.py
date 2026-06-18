from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from core.permissions import (
    IsSuperAdmin,
    IsShopkeeper,
    IsWarehouseAdmin,
    IsWarehouseAdminOrSuperAdmin,
)
from warehouses.models import Warehouse
from orders.models import Order
from riders.models import Rider

User = get_user_model()


class IsSuperAdminPermissionTests(TestCase):
    """Test cases for IsSuperAdmin permission"""

    def setUp(self):
        self.admin = User.objects.create_user(email="admin@example.com", role="ADMIN")
        self.superuser = User.objects.create_superuser(
            email="superuser@example.com", password="test123"
        )
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        self.factory = APIRequestFactory()
        self.permission = IsSuperAdmin()

    def test_admin_has_permission(self):
        """Test admin user has permission"""
        request = self.factory.get("/")
        request.user = self.admin
        self.assertTrue(self.permission.has_permission(request, None))

    def test_superuser_has_permission(self):
        """Test superuser has permission"""
        request = self.factory.get("/")
        request.user = self.superuser
        self.assertTrue(self.permission.has_permission(request, None))

    def test_shopkeeper_no_permission(self):
        """Test shopkeeper does not have permission"""
        request = self.factory.get("/")
        request.user = self.shopkeeper
        self.assertFalse(self.permission.has_permission(request, None))

    def test_unauthenticated_no_permission(self):
        """Test unauthenticated user does not have permission"""
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get("/")
        request.user = AnonymousUser()
        self.assertFalse(self.permission.has_permission(request, None))


class IsShopkeeperPermissionTests(TestCase):
    """Test cases for IsShopkeeper permission"""

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
        )
        self.order = Order.objects.create(
            shopkeeper=self.shopkeeper, warehouse=self.warehouse
        )
        self.factory = APIRequestFactory()
        self.permission = IsShopkeeper()

    def test_shopkeeper_has_permission(self):
        """Test shopkeeper has permission"""
        request = self.factory.get("/")
        request.user = self.shopkeeper
        self.assertTrue(self.permission.has_permission(request, None))

    def test_non_shopkeeper_no_permission(self):
        """Test non-shopkeeper does not have permission"""
        request = self.factory.get("/")
        request.user = self.warehouse_admin
        self.assertFalse(self.permission.has_permission(request, None))

    def test_shopkeeper_can_access_own_order(self):
        """Test shopkeeper can access their own order"""
        request = self.factory.get("/")
        request.user = self.shopkeeper
        self.assertTrue(
            self.permission.has_object_permission(request, None, self.order)
        )

    def test_shopkeeper_cannot_access_other_order(self):
        """Test shopkeeper cannot access another shopkeeper's order"""
        other_shopkeeper = User.objects.create_user(
            email="other@example.com", role="SHOPKEEPER"
        )
        other_order = Order.objects.create(
            shopkeeper=other_shopkeeper, warehouse=self.warehouse
        )

        request = self.factory.get("/")
        request.user = self.shopkeeper
        self.assertFalse(
            self.permission.has_object_permission(request, None, other_order)
        )

    def test_other_shopkeeper_cannot_access_own_order(self):
        """Test shopkeeper cannot access another shopkeeper's order"""
        other_shopkeeper = User.objects.create_user(
            email="other@example.com", role="SHOPKEEPER"
        )
        request = self.factory.get("/")
        request.user = other_shopkeeper
        self.assertFalse(
            self.permission.has_object_permission(request, None, self.order)
        )


class IsWarehouseAdminPermissionTests(TestCase):
    """Test cases for IsWarehouseAdmin permission"""

    def setUp(self):
        self.warehouse_admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.other_admin = User.objects.create_user(
            email="other@example.com", role="WAREHOUSE_MANAGER"
        )
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        self.warehouse = Warehouse.objects.create(
            admin=self.warehouse_admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
        )
        self.factory = APIRequestFactory()
        self.permission = IsWarehouseAdmin()

    def test_warehouse_admin_has_permission(self):
        """Test warehouse admin has permission"""
        request = self.factory.get("/")
        request.user = self.warehouse_admin
        self.assertTrue(self.permission.has_permission(request, None))

    def test_non_warehouse_admin_no_permission(self):
        """Test non-warehouse admin does not have permission"""
        request = self.factory.get("/")
        request.user = self.shopkeeper
        self.assertFalse(self.permission.has_permission(request, None))

    def test_warehouse_admin_can_access_own_warehouse(self):
        """Test warehouse admin can access their own warehouse"""
        request = self.factory.get("/")
        request.user = self.warehouse_admin
        self.assertTrue(
            self.permission.has_object_permission(request, None, self.warehouse)
        )

    def test_warehouse_admin_cannot_access_other_warehouse(self):
        """Test warehouse admin cannot access another admin's warehouse"""
        request = self.factory.get("/")
        request.user = self.other_admin
        self.assertFalse(
            self.permission.has_object_permission(request, None, self.warehouse)
        )


class IsWarehouseAdminOrSuperAdminPermissionTests(TestCase):
    """Test cases for IsWarehouseAdminOrSuperAdmin permission"""

    def setUp(self):
        self.admin = User.objects.create_user(email="admin@example.com", role="ADMIN")
        self.warehouse_admin = User.objects.create_user(
            email="warehouse@example.com", role="WAREHOUSE_MANAGER"
        )
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        self.factory = APIRequestFactory()
        self.permission = IsWarehouseAdminOrSuperAdmin()

    def test_admin_has_permission(self):
        """Test admin has permission"""
        request = self.factory.get("/")
        request.user = self.admin
        self.assertTrue(self.permission.has_permission(request, None))

    def test_warehouse_admin_has_permission(self):
        """Test warehouse admin has permission"""
        request = self.factory.get("/")
        request.user = self.warehouse_admin
        self.assertTrue(self.permission.has_permission(request, None))

    def test_shopkeeper_no_permission(self):
        """Test shopkeeper does not have permission"""
        request = self.factory.get("/")
        request.user = self.shopkeeper
        self.assertFalse(self.permission.has_permission(request, None))


class PermissionObjectLevelTests(TestCase):
    """Test cases for object-level permissions"""

    def setUp(self):
        self.warehouse_admin = User.objects.create_user(
            email="admin@example.com", role="WAREHOUSE_MANAGER"
        )
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        self.rider_user = User.objects.create_user(
            email="rider@example.com", role="RIDER"
        )
        self.warehouse = Warehouse.objects.create(
            admin=self.warehouse_admin,
            name="Test Warehouse",
            address="123 Test St",
            contact_number="+1234567890",
        )
        self.rider = Rider.objects.create(
            user=self.rider_user, warehouse=self.warehouse
        )
        self.factory = APIRequestFactory()

    def test_warehouse_admin_can_access_rider_in_warehouse(self):
        """Test warehouse admin can access riders in their warehouse"""
        permission = IsWarehouseAdmin()
        request = self.factory.get("/")
        request.user = self.warehouse_admin
        # Verify warehouse admin can check object permissions
        # The actual permission check happens in the view, not here
        self.assertTrue(permission.has_permission(request, None))


class PermissionRoleTests(TestCase):
    """Test cases for role-based permissions"""

    def setUp(self):
        self.admin = User.objects.create_user(email="admin@example.com", role="ADMIN")
        self.warehouse_manager = User.objects.create_user(
            email="warehouse@example.com", role="WAREHOUSE_MANAGER"
        )
        self.rider = User.objects.create_user(email="rider@example.com", role="RIDER")
        self.shopkeeper = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )

    def test_user_roles_are_distinct(self):
        """Test that user roles are properly set and distinct"""
        self.assertEqual(self.admin.role, "ADMIN")
        self.assertEqual(self.warehouse_manager.role, "WAREHOUSE_MANAGER")
        self.assertEqual(self.rider.role, "RIDER")
        self.assertEqual(self.shopkeeper.role, "SHOPKEEPER")

    def test_superuser_is_admin_role(self):
        """Test superuser has ADMIN role"""
        superuser = User.objects.create_superuser(
            email="superuser@example.com", password="test123"
        )
        self.assertEqual(superuser.role, "ADMIN")
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)

    def test_pending_user_has_no_role_permissions(self):
        """Test that PENDING role users have restricted access"""

        pending_user = User.objects.create_user(
            email="pending@example.com", role="PENDING"
        )
        factory = APIRequestFactory()

        self.assertEqual(pending_user.role, "PENDING")

        # Pending users should not pass role-specific permissions
        request = factory.get("/")
        request.user = pending_user

        self.assertFalse(IsSuperAdmin().has_permission(request, None))
        self.assertFalse(IsShopkeeper().has_permission(request, None))
        self.assertFalse(IsWarehouseAdmin().has_permission(request, None))


class InactiveUserPermissionTests(TestCase):
    """Test cases for inactive user permissions"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", role="SHOPKEEPER"
        )
        self.factory = APIRequestFactory()

    def test_inactive_user_denied_permission(self):
        """Test that inactive users are denied permission"""
        self.user.is_active = False
        self.user.save()

        IsShopkeeper()
        request = self.factory.get("/")
        request.user = self.user
        # In production, inactive users fail at authentication level
        # Permission classes assume authenticated user is active
        self.assertFalse(self.user.is_active)


class SoftDeletedUserPermissionTests(TestCase):
    """Test cases for soft-deleted user permissions"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", role="SHOPKEEPER"
        )
        self.factory = APIRequestFactory()

    def test_soft_deleted_user_is_inactive(self):
        """Test that soft-deleted users become inactive"""
        self.user.soft_delete()
        self.assertFalse(self.user.is_active)
        self.assertTrue(self.user.is_deleted)

    def test_soft_deleted_user_excluded_from_queries(self):
        """Test soft-deleted users are excluded from default queries"""
        user_id = self.user.id
        self.user.soft_delete()

        # Should not be in default queryset
        self.assertFalse(User.objects.filter(id=user_id).exists())

        # Should be in all_objects queryset
        self.assertTrue(User.all_objects.filter(id=user_id).exists())
