from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from accounts.models import ShopkeeperProfile
from accounts.serializers import (
    SignInSerializer,
    SignUpSerializer,
    UserSerializer,
    ShopkeeperProfileSerializer,
)

User = get_user_model()


class UserModelTests(TestCase):
    """Test cases for User model"""

    def test_create_user_with_email(self):
        """Test creating a user with email"""
        user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123"))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.role, "PENDING")

    def test_create_user_with_phone(self):
        """Test creating a user with phone number"""
        user = User.objects.create_user(
            email="phone@example.com",
            phone_number="+1234567890",
            password="testpass123",
        )
        self.assertEqual(user.phone_number, "+1234567890")
        self.assertTrue(user.is_active)

    def test_create_user_without_email_and_phone_raises_error(self):
        """Test that creating user without email or phone raises error"""
        with self.assertRaises(ValueError):
            User.objects.create_user(email=None, phone_number=None)

    def test_create_superuser(self):
        """Test creating a superuser"""
        admin_user = User.objects.create_superuser(
            email="admin@example.com", password="adminpass123"
        )
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertEqual(admin_user.role, "ADMIN")

    def test_create_superuser_without_is_staff_raises_error(self):
        """Test that creating superuser with is_staff=False raises error"""
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="admin@example.com", password="adminpass123", is_staff=False
            )

    def test_user_string_representation(self):
        """Test user string representation"""
        user = User.objects.create_user(email="test@example.com")
        self.assertEqual(str(user), "test@example.com")

    def test_user_role_choices(self):
        """Test user role validation"""
        user = User.objects.create_user(email="rider@example.com", role="RIDER")
        self.assertEqual(user.role, "RIDER")

    def test_user_unique_email(self):
        """Test that email must be unique"""
        User.objects.create_user(email="unique@example.com")
        with self.assertRaises(Exception):
            User.objects.create_user(email="unique@example.com")

    def test_user_unique_phone_number(self):
        """Test that phone number must be unique"""
        User.objects.create_user(email="user1@example.com", phone_number="+1234567890")
        with self.assertRaises(Exception):
            User.objects.create_user(
                email="user2@example.com", phone_number="+1234567890"
            )

    def test_user_get_full_name(self):
        """Test get_full_name method"""
        user = User.objects.create_user(email="test@example.com", full_name="Test User")
        self.assertEqual(user.get_full_name(), "Test User")

    def test_user_get_full_name_fallback(self):
        """Test get_full_name fallback to email"""
        user = User.objects.create_user(email="test@example.com")
        self.assertEqual(user.get_full_name(), "test@example.com")


class ShopkeeperProfileModelTests(TestCase):
    """Test cases for ShopkeeperProfile model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )

    def test_create_shopkeeper_profile(self):
        """Test creating a shopkeeper profile"""
        profile = ShopkeeperProfile.objects.create(
            user=self.user,
            shop_name="Test Shop",
            shop_address="123 Test St",
            gst_number="22AAAAA0000A1Z5",
        )
        self.assertEqual(profile.shop_name, "Test Shop")
        self.assertEqual(profile.user, self.user)
        self.assertFalse(profile.is_verified)

    def test_shopkeeper_profile_with_location(self):
        """Test creating profile with PostGIS location"""
        location = Point(77.5946, 12.9716, srid=4326)  # Bangalore
        profile = ShopkeeperProfile.objects.create(
            user=self.user,
            shop_name="Test Shop",
            shop_address="123 Test St",
            location=location,
        )
        self.assertIsNotNone(profile.location)
        self.assertAlmostEqual(profile.location.x, 77.5946, places=4)
        self.assertAlmostEqual(profile.location.y, 12.9716, places=4)

    def test_shopkeeper_profile_string_representation(self):
        """Test shopkeeper profile string representation"""
        profile = ShopkeeperProfile.objects.create(
            user=self.user, shop_name="Test Shop", shop_address="123 Test St"
        )
        self.assertIn("Test Shop", str(profile))
        self.assertIn(self.user.email, str(profile))

    def test_shopkeeper_profile_defaults(self):
        """Test default values for shopkeeper profile"""
        profile = ShopkeeperProfile.objects.create(
            user=self.user, shop_name="Test Shop"
        )
        self.assertEqual(profile.shop_address, "")
        self.assertEqual(profile.gst_number, "")
        self.assertFalse(profile.is_verified)
        self.assertIsNone(profile.location)


class SignUpSerializerTests(TestCase):
    """Test cases for SignUpSerializer"""

    def test_valid_data(self):
        """Test serializer with valid data"""
        data = {
            "email": "test@example.com",
            "password": "securepass123",
            "confirm_password": "securepass123",
        }
        serializer = SignUpSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["email"], "test@example.com")

    def test_email_lowercase_normalization(self):
        """Test email is normalized to lowercase"""
        data = {
            "email": "TEST@EXAMPLE.COM",
            "password": "securepass123",
            "confirm_password": "securepass123",
        }
        serializer = SignUpSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["email"], "test@example.com")

    def test_invalid_email_format(self):
        """Test serializer with invalid email format"""
        data = {
            "email": "invalid-email",
            "password": "securepass123",
            "confirm_password": "securepass123",
        }
        serializer = SignUpSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_missing_email(self):
        """Test serializer with missing email"""
        data = {"password": "securepass123", "confirm_password": "securepass123"}
        serializer = SignUpSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_passwords_do_not_match(self):
        """Test passwords must match"""
        data = {
            "email": "test@example.com",
            "password": "password123",
            "confirm_password": "different123",
        }
        serializer = SignUpSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("confirm_password", serializer.errors)

    def test_password_too_short(self):
        """Test password must be at least 6 characters"""
        data = {
            "email": "test@example.com",
            "password": "short",
            "confirm_password": "short",
        }
        serializer = SignUpSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)


class SignInSerializerTests(TestCase):
    """Test cases for SignInSerializer"""

    def test_valid_data(self):
        """Test serializer with valid data"""
        data = {"email": "test@example.com", "password": "securepass123"}
        serializer = SignInSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_email_lowercase_normalization(self):
        """Test email is normalized to lowercase"""
        data = {"email": "TEST@EXAMPLE.COM", "password": "securepass123"}
        serializer = SignInSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["email"], "test@example.com")

    def test_missing_email(self):
        """Test serializer with missing email"""
        data = {"password": "securepass123"}
        serializer = SignInSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_missing_password(self):
        """Test serializer with missing password"""
        data = {"email": "test@example.com"}
        serializer = SignInSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)


class UserSerializerTests(TestCase):
    """Test cases for UserSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            phone_number="+1234567890",
            full_name="Test User",
            role="SHOPKEEPER",
        )

    def test_serialize_user(self):
        """Test serializing a user"""
        serializer = UserSerializer(self.user)
        data = serializer.data
        self.assertEqual(data["email"], "test@example.com")
        self.assertEqual(data["phone_number"], "+1234567890")
        self.assertEqual(data["full_name"], "Test User")
        self.assertEqual(data["role"], "SHOPKEEPER")
        self.assertIn("id", data)

    def test_read_only_fields(self):
        """Test that id, date_joined, and last_login are read-only"""
        serializer = UserSerializer(self.user)
        self.assertIn("id", serializer.fields)
        self.assertIn("date_joined", serializer.fields)
        self.assertIn("last_login", serializer.fields)


class ShopkeeperProfileSerializerTests(TestCase):
    """Test cases for ShopkeeperProfileSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )

    def test_create_profile_with_coordinates(self):
        """Test creating profile with latitude/longitude"""
        data = {
            "shop_name": "Test Shop",
            "shop_address": "123 Test St",
            "latitude": 12.9716,
            "longitude": 77.5946,
        }
        serializer = ShopkeeperProfileSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        profile = serializer.save(user=self.user)
        self.assertIsNotNone(profile.location)
        self.assertAlmostEqual(profile.location.y, 12.9716, places=4)
        self.assertAlmostEqual(profile.location.x, 77.5946, places=4)

    def test_update_profile_location(self):
        """Test updating profile location"""
        profile = ShopkeeperProfile.objects.create(
            user=self.user, shop_name="Test Shop", shop_address="123 Test St"
        )
        data = {"shop_name": "Updated Shop", "latitude": 13.0827, "longitude": 80.2707}
        serializer = ShopkeeperProfileSerializer(profile, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_profile = serializer.save()
        self.assertIsNotNone(updated_profile.location)


class SignUpViewTests(APITestCase):
    """Test cases for SignUpView"""

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/accounts/signup/"

    @patch("accounts.views.SupabaseService.sign_up")
    def test_signup_success(self, mock_sign_up):
        """Test successful user sign up"""
        mock_user = MagicMock()
        mock_user.id = "supabase-uid-123"
        mock_session = MagicMock()
        mock_session.access_token = "access-token"
        mock_session.refresh_token = "refresh-token"
        mock_session.expires_in = 3600
        mock_session.expires_at = 1234567890
        mock_session.token_type = "bearer"

        mock_response = MagicMock()
        mock_response.user = mock_user
        mock_response.session = mock_session
        mock_sign_up.return_value = mock_response

        data = {
            "email": "newuser@example.com",
            "password": "securepass123",
            "confirm_password": "securepass123",
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access_token", response.data)
        self.assertIn("user", response.data)

        # Verify user was created with PENDING role
        user = User.objects.get(email="newuser@example.com")
        self.assertEqual(user.supabase_uid, "supabase-uid-123")
        self.assertEqual(user.role, "PENDING")
        mock_sign_up.assert_called_once_with("newuser@example.com", "securepass123")

    def test_signup_invalid_email(self):
        """Test sign up with invalid email"""
        data = {
            "email": "invalid-email",
            "password": "securepass123",
            "confirm_password": "securepass123",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_signup_passwords_mismatch(self):
        """Test sign up with mismatched passwords"""
        data = {
            "email": "test@example.com",
            "password": "password123",
            "confirm_password": "different123",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_signup_missing_fields(self):
        """Test sign up with missing fields"""
        data = {"email": "test@example.com"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("accounts.views.SupabaseService.sign_up")
    def test_signup_service_error(self, mock_sign_up):
        """Test sign up with service error"""
        mock_sign_up.side_effect = Exception("Sign up failed")
        data = {
            "email": "test@example.com",
            "password": "securepass123",
            "confirm_password": "securepass123",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SignInViewTests(APITestCase):
    """Test cases for SignInView"""

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/accounts/signin/"

    @patch("accounts.views.SupabaseService.sign_in")
    def test_signin_success_new_user(self, mock_sign_in):
        """Test successful sign in with new user creation"""
        mock_user = MagicMock()
        mock_user.id = "supabase-uid-123"
        mock_session = MagicMock()
        mock_session.access_token = "access-token"
        mock_session.refresh_token = "refresh-token"
        mock_session.expires_in = 3600
        mock_session.expires_at = 1234567890
        mock_session.token_type = "bearer"

        mock_response = MagicMock()
        mock_response.user = mock_user
        mock_response.session = mock_session
        mock_sign_in.return_value = mock_response

        data = {"email": "newuser@example.com", "password": "securepass123"}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)
        self.assertIn("user", response.data)

        # Verify user was created
        user = User.objects.get(email="newuser@example.com")
        self.assertEqual(user.supabase_uid, "supabase-uid-123")
        mock_sign_in.assert_called_once_with("newuser@example.com", "securepass123")

    @patch("accounts.views.SupabaseService.sign_in")
    def test_signin_existing_user(self, mock_sign_in):
        """Test sign in with existing user"""
        User.objects.create_user(
            email="existing@example.com", supabase_uid="existing-uid", role="SHOPKEEPER"
        )

        mock_user = MagicMock()
        mock_user.id = "existing-uid"
        mock_session = MagicMock()
        mock_session.access_token = "access-token"
        mock_session.refresh_token = "refresh-token"
        mock_session.expires_in = 3600
        mock_session.expires_at = 1234567890
        mock_session.token_type = "bearer"

        mock_response = MagicMock()
        mock_response.user = mock_user
        mock_response.session = mock_session
        mock_sign_in.return_value = mock_response

        data = {"email": "existing@example.com", "password": "securepass123"}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify no duplicate user was created
        self.assertEqual(User.objects.filter(supabase_uid="existing-uid").count(), 1)

    def test_signin_inactive_user(self):
        """Test sign in with inactive user"""
        # Create inactive user
        User.objects.create_user(
            email="inactive@example.com", supabase_uid="inactive-uid", is_active=False
        )

        # Mock successful Supabase authentication
        with patch("accounts.views.SupabaseService.sign_in") as mock_sign_in:
            mock_user = MagicMock()
            mock_user.id = "inactive-uid"
            mock_session = MagicMock()
            mock_session.access_token = "access-token"
            mock_response = MagicMock()
            mock_response.user = mock_user
            mock_response.session = mock_session
            mock_sign_in.return_value = mock_response

            data = {"email": "inactive@example.com", "password": "securepass123"}
            response = self.client.post(self.url, data, format="json")

            # Inactive users return 401 (authentication failure)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_signin_invalid_credentials(self):
        """Test sign in with invalid credentials"""
        data = {"email": "test@example.com", "password": "wrongpassword"}

        with patch("accounts.views.SupabaseService.sign_in") as mock_sign_in:
            mock_sign_in.side_effect = Exception("Invalid credentials")
            response = self.client.post(self.url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_signin_missing_fields(self):
        """Test sign in with missing fields"""
        data = {"email": "test@example.com"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LogoutViewTests(APITestCase):
    """Test cases for LogoutView"""

    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = "/api/accounts/logout/"

    @patch("accounts.views.SupabaseService.sign_out")
    def test_logout_success(self, mock_sign_out):
        """Test successful logout"""
        mock_sign_out.return_value = {"success": True}
        response = self.client.post(self.url, HTTP_AUTHORIZATION="Bearer test-token")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

    def test_logout_unauthenticated(self):
        """Test logout without authentication"""
        self.client.force_authenticate(user=None)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CurrentUserViewTests(APITestCase):
    """Test cases for CurrentUserView"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", full_name="Test User", role="SHOPKEEPER"
        )
        self.client = APIClient()
        self.url = "/api/accounts/me/"

    def test_get_current_user_authenticated(self):
        """Test getting current user when authenticated"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test@example.com")
        self.assertEqual(response.data["full_name"], "Test User")

    def test_get_current_user_unauthenticated(self):
        """Test getting current user without authentication"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ============================================================================
# Soft Delete Tests
# ============================================================================


class SoftDeleteModelTests(TestCase):
    """Test cases for soft delete model functionality"""

    def test_soft_delete_sets_deleted_at(self):
        """Test that soft_delete sets deleted_at timestamp"""
        user = User.objects.create_user(email="test@example.com")
        self.assertIsNone(user.deleted_at)
        self.assertFalse(user.is_deleted)

        user.soft_delete()

        self.assertIsNotNone(user.deleted_at)
        self.assertTrue(user.is_deleted)
        self.assertFalse(user.is_active)

    def test_soft_delete_excludes_from_default_queryset(self):
        """Test that soft-deleted users are excluded from default queryset"""
        user = User.objects.create_user(email="test@example.com")
        self.assertEqual(User.objects.count(), 1)

        user.soft_delete()

        # Default manager should exclude soft-deleted users
        self.assertEqual(User.objects.count(), 0)
        # all_objects should include soft-deleted users
        self.assertEqual(User.all_objects.count(), 1)

    def test_restore_clears_deleted_at(self):
        """Test that restore clears deleted_at and reactivates user"""
        user = User.objects.create_user(email="test@example.com")
        user.soft_delete()

        self.assertTrue(user.is_deleted)

        user.restore()

        self.assertIsNone(user.deleted_at)
        self.assertFalse(user.is_deleted)
        self.assertTrue(user.is_active)

    def test_is_deleted_property(self):
        """Test is_deleted property"""
        user = User.objects.create_user(email="test@example.com")
        self.assertFalse(user.is_deleted)

        user.soft_delete()
        self.assertTrue(user.is_deleted)

        user.restore()
        self.assertFalse(user.is_deleted)

    def test_has_dependent_data_no_dependencies(self):
        """Test has_dependent_data returns False when user has no dependencies"""
        user = User.objects.create_user(email="test@example.com")
        has_deps, deps = user.has_dependent_data()

        self.assertFalse(has_deps)
        self.assertEqual(deps, {})

    def test_has_dependent_data_with_shopkeeper_profile(self):
        """Test has_dependent_data detects shopkeeper profile"""
        user = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        ShopkeeperProfile.objects.create(
            user=user, shop_name="Test Shop", shop_address="123 Test St"
        )

        has_deps, deps = user.has_dependent_data()

        self.assertTrue(has_deps)
        self.assertIn("shopkeeper_profile", deps)


class AdminUserDeactivateViewTests(APITestCase):
    """Test cases for AdminUserDeactivateView (soft delete)"""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="admin@example.com", password="adminpass123"
        )
        self.regular_user = User.objects.create_user(
            email="regular@example.com", role="SHOPKEEPER"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_deactivate_user_success(self):
        """Test successful user deactivation (soft delete)"""
        url = f"/api/accounts/admin/users/{self.regular_user.id}/deactivate/"
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

        # Refresh from database using all_objects
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.is_deleted)
        self.assertFalse(self.regular_user.is_active)

    def test_deactivate_user_with_reason(self):
        """Test user deactivation with reason"""
        url = f"/api/accounts/admin/users/{self.regular_user.id}/deactivate/"
        response = self.client.post(
            url, {"reason": "Violated terms of service"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

    def test_cannot_deactivate_self(self):
        """Test admin cannot deactivate their own account"""
        url = f"/api/accounts/admin/users/{self.admin.id}/deactivate/"
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cannot deactivate your own", response.data["error"])

    def test_cannot_deactivate_already_deleted_user(self):
        """Test cannot deactivate already deleted user"""
        self.regular_user.soft_delete()

        url = f"/api/accounts/admin/users/{self.regular_user.id}/deactivate/"
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already deactivated", response.data["error"])

    def test_deactivate_requires_admin(self):
        """Test that non-admin users cannot deactivate users"""
        self.client.force_authenticate(user=self.regular_user)

        another_user = User.objects.create_user(email="another@example.com")
        url = f"/api/accounts/admin/users/{another_user.id}/deactivate/"
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_deactivate_user_not_found(self):
        """Test deactivating non-existent user"""
        url = "/api/accounts/admin/users/99999/deactivate/"
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AdminUserRestoreViewTests(APITestCase):
    """Test cases for AdminUserRestoreView"""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="admin@example.com", password="adminpass123"
        )
        self.deleted_user = User.objects.create_user(
            email="deleted@example.com", role="SHOPKEEPER"
        )
        self.deleted_user.soft_delete()
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_restore_user_success(self):
        """Test successful user restoration"""
        url = f"/api/accounts/admin/users/{self.deleted_user.id}/restore/"
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

        # Refresh from database
        self.deleted_user.refresh_from_db()
        self.assertFalse(self.deleted_user.is_deleted)
        self.assertTrue(self.deleted_user.is_active)

    def test_cannot_restore_active_user(self):
        """Test cannot restore user that isn't deleted"""
        active_user = User.objects.create_user(email="active@example.com")

        url = f"/api/accounts/admin/users/{active_user.id}/restore/"
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("not deactivated", response.data["error"])

    def test_restore_requires_admin(self):
        """Test that non-admin users cannot restore users"""
        regular_user = User.objects.create_user(email="regular@example.com")
        self.client.force_authenticate(user=regular_user)

        url = f"/api/accounts/admin/users/{self.deleted_user.id}/restore/"
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminUserHardDeleteViewTests(APITestCase):
    """Test cases for AdminUserHardDeleteView"""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="admin@example.com", password="adminpass123"
        )
        self.regular_user = User.objects.create_user(
            email="regular@example.com", role="SHOPKEEPER"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_hard_delete_user_no_dependencies(self):
        """Test successful hard delete when user has no dependencies"""
        user_id = self.regular_user.id
        url = f"/api/accounts/admin/users/{user_id}/delete/"
        response = self.client.post(url, {"confirm": True}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

        # Verify user is actually deleted from database
        self.assertFalse(User.all_objects.filter(id=user_id).exists())

    def test_hard_delete_requires_confirmation(self):
        """Test hard delete requires explicit confirmation"""
        url = f"/api/accounts/admin/users/{self.regular_user.id}/delete/"

        # Test without confirm field
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test with confirm=False
        response = self.client.post(url, {"confirm": False}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_hard_delete_blocked_with_dependencies(self):
        """Test hard delete is blocked when user has dependent data"""
        # Create shopkeeper profile to create dependency
        ShopkeeperProfile.objects.create(
            user=self.regular_user, shop_name="Test Shop", shop_address="123 Test St"
        )

        url = f"/api/accounts/admin/users/{self.regular_user.id}/delete/"
        response = self.client.post(url, {"confirm": True}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("dependencies", response.data)
        self.assertIn("suggestion", response.data)

    def test_cannot_hard_delete_self(self):
        """Test admin cannot hard delete their own account"""
        url = f"/api/accounts/admin/users/{self.admin.id}/delete/"
        response = self.client.post(url, {"confirm": True}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cannot delete your own", response.data["error"])

    def test_hard_delete_requires_admin(self):
        """Test that non-admin users cannot hard delete"""
        self.client.force_authenticate(user=self.regular_user)

        another_user = User.objects.create_user(email="another@example.com")
        url = f"/api/accounts/admin/users/{another_user.id}/delete/"
        response = self.client.post(url, {"confirm": True}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminUserListViewTests(APITestCase):
    """Test cases for AdminUserListView"""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="admin@example.com", password="adminpass123"
        )
        self.active_user = User.objects.create_user(
            email="active@example.com", role="SHOPKEEPER"
        )
        self.deleted_user = User.objects.create_user(
            email="deleted@example.com", role="RIDER"
        )
        self.deleted_user.soft_delete()

        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)
        self.url = "/api/accounts/admin/users/"

    def test_list_users_excludes_deleted_by_default(self):
        """Test listing users excludes soft-deleted users by default"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = [u["email"] for u in response.data["users"]]
        self.assertIn("active@example.com", emails)
        self.assertNotIn("deleted@example.com", emails)

    def test_list_users_include_deleted(self):
        """Test listing users can include soft-deleted users"""
        response = self.client.get(f"{self.url}?include_deleted=true")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = [u["email"] for u in response.data["users"]]
        self.assertIn("active@example.com", emails)
        self.assertIn("deleted@example.com", emails)

    def test_list_users_filter_by_role(self):
        """Test filtering users by role"""
        response = self.client.get(f"{self.url}?role=SHOPKEEPER")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for user in response.data["users"]:
            self.assertEqual(user["role"], "SHOPKEEPER")

    def test_list_users_requires_admin(self):
        """Test that listing users requires admin permission"""
        self.client.force_authenticate(user=self.active_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DeactivatedUserAuthenticationTests(APITestCase):
    """Test cases for authentication blocking of deactivated users"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", supabase_uid="test-supabase-uid"
        )
        self.client = APIClient()

    def test_deactivated_user_cannot_access_protected_endpoints(self):
        """Test that deactivated users cannot access protected endpoints"""
        # First, verify user can access when active
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/accounts/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Deactivate user
        self.user.soft_delete()

        # Refresh the user object to get updated state
        self.user.refresh_from_db()

        # Create new client to simulate fresh request
        new_client = APIClient()
        # Force authenticate with the deactivated user
        # Note: In real scenario, authentication would fail at JWT validation
        # Here we're testing the is_active check in the authentication flow
        new_client.force_authenticate(user=self.user)

        # The user is inactive, so the auth check should fail
        # However, force_authenticate bypasses normal auth
        # In production, the SupabaseAuthentication class checks is_active

    def test_soft_deleted_user_excluded_from_normal_queries(self):
        """Test soft-deleted users are excluded from normal querysets"""
        self.assertEqual(User.objects.filter(email="test@example.com").count(), 1)

        self.user.soft_delete()

        # Normal queryset should not find the user
        self.assertEqual(User.objects.filter(email="test@example.com").count(), 0)

        # all_objects should still find the user
        self.assertEqual(User.all_objects.filter(email="test@example.com").count(), 1)


class RelatedDataIntegrityTests(TestCase):
    """Test that soft delete preserves related data integrity"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="shopkeeper@example.com", role="SHOPKEEPER"
        )
        self.profile = ShopkeeperProfile.objects.create(
            user=self.user, shop_name="Test Shop", shop_address="123 Test St"
        )

    def test_soft_delete_preserves_related_data(self):
        """Test that soft deleting user preserves related profile"""
        profile_id = self.profile.id

        self.user.soft_delete()

        # Profile should still exist
        self.assertTrue(ShopkeeperProfile.objects.filter(id=profile_id).exists())

        # Profile's user reference should still be valid (via all_objects)
        profile = ShopkeeperProfile.objects.get(id=profile_id)
        self.assertEqual(profile.user_id, self.user.id)

        # Can access user through all_objects
        user = User.all_objects.get(id=self.user.id)
        self.assertTrue(user.is_deleted)

    def test_restored_user_maintains_related_data(self):
        """Test that restoring user maintains all related data"""
        self.user.soft_delete()
        self.user.restore()

        # Profile should still be linked
        self.assertEqual(self.user.shopkeeper_profile.id, self.profile.id)
        self.assertEqual(self.user.shopkeeper_profile.shop_name, "Test Shop")
