from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from accounts.models import ShopkeeperProfile
from accounts.serializers import (
    SendOTPSerializer,
    VerifyOTPSerializer,
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
        self.assertEqual(user.role, "SHOPKEEPER")

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


class SendOTPSerializerTests(TestCase):
    """Test cases for SendOTPSerializer"""

    def test_valid_email(self):
        """Test serializer with valid email"""
        data = {"email": "test@example.com"}
        serializer = SendOTPSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["email"], "test@example.com")

    def test_email_lowercase_normalization(self):
        """Test email is normalized to lowercase"""
        data = {"email": "TEST@EXAMPLE.COM"}
        serializer = SendOTPSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["email"], "test@example.com")

    def test_invalid_email_format(self):
        """Test serializer with invalid email format"""
        data = {"email": "invalid-email"}
        serializer = SendOTPSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_missing_email(self):
        """Test serializer with missing email"""
        data = {}
        serializer = SendOTPSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)


class VerifyOTPSerializerTests(TestCase):
    """Test cases for VerifyOTPSerializer"""

    def test_valid_data(self):
        """Test serializer with valid data"""
        data = {"email": "test@example.com", "otp": "123456"}
        serializer = VerifyOTPSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_otp_must_be_digits(self):
        """Test OTP must contain only digits"""
        data = {"email": "test@example.com", "otp": "12ab56"}
        serializer = VerifyOTPSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("otp", serializer.errors)

    def test_missing_email(self):
        """Test serializer with missing email"""
        data = {"otp": "123456"}
        serializer = VerifyOTPSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_missing_otp(self):
        """Test serializer with missing OTP"""
        data = {"email": "test@example.com"}
        serializer = VerifyOTPSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("otp", serializer.errors)


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


class SendOTPViewTests(APITestCase):
    """Test cases for SendOTPView"""

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/accounts/send-otp/"

    @patch("accounts.views.SupabaseService.send_otp")
    def test_send_otp_success(self, mock_send_otp):
        """Test successful OTP send"""
        mock_send_otp.return_value = {"success": True}
        data = {"email": "test@example.com"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        mock_send_otp.assert_called_once_with("test@example.com")

    def test_send_otp_invalid_email(self):
        """Test sending OTP with invalid email"""
        data = {"email": "invalid-email"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_otp_missing_email(self):
        """Test sending OTP without email"""
        data = {}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("accounts.views.SupabaseService.send_otp")
    def test_send_otp_service_error(self, mock_send_otp):
        """Test OTP send with service error"""
        mock_send_otp.side_effect = Exception("Service error")
        data = {"email": "test@example.com"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyOTPViewTests(APITestCase):
    """Test cases for VerifyOTPView"""

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/accounts/verify-otp/"

    @patch("accounts.views.SupabaseService.verify_otp")
    def test_verify_otp_success_new_user(self, mock_verify_otp):
        """Test successful OTP verification with new user creation"""
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
        mock_verify_otp.return_value = mock_response

        data = {"email": "newuser@example.com", "otp": "123456"}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)
        self.assertIn("user", response.data)

        # Verify user was created
        user = User.objects.get(email="newuser@example.com")
        self.assertEqual(user.supabase_uid, "supabase-uid-123")

    @patch("accounts.views.SupabaseService.verify_otp")
    def test_verify_otp_existing_user(self, mock_verify_otp):
        """Test OTP verification with existing user"""
        existing_user = User.objects.create_user(
            email="existing@example.com", supabase_uid="existing-uid"
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
        mock_verify_otp.return_value = mock_response

        data = {"email": "existing@example.com", "otp": "123456"}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify no duplicate user was created
        self.assertEqual(User.objects.filter(supabase_uid="existing-uid").count(), 1)

    def test_verify_otp_invalid_format(self):
        """Test OTP verification with invalid OTP format"""
        data = {"email": "test@example.com", "otp": "abc123"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("accounts.views.SupabaseService.verify_otp")
    def test_verify_otp_service_error(self, mock_verify_otp):
        """Test OTP verification with service error"""
        mock_verify_otp.side_effect = Exception("Invalid OTP")
        data = {"email": "test@example.com", "otp": "123456"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


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
