from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import ShopkeeperProfile
from unittest.mock import patch, MagicMock

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for the User model"""

    def test_create_user(self):
        """Test creating a user with phone number"""
        user = User.objects.create_user(
            phone_number="+1234567890", full_name="Test User", role="SHOPKEEPER"
        )
        self.assertEqual(user.phone_number, "+1234567890")
        self.assertEqual(user.full_name, "Test User")
        self.assertEqual(user.role, "SHOPKEEPER")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        """Test creating a superuser"""
        user = User.objects.create_superuser(
            phone_number="+1234567890", password="testpass123"
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertEqual(user.role, "ADMIN")

    def test_user_string_representation(self):
        """Test user string representation"""
        user = User.objects.create_user(phone_number="+1234567890")
        self.assertEqual(str(user), "+1234567890")


class ShopkeeperProfileModelTest(TestCase):
    """Test cases for ShopkeeperProfile model"""

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+1234567890", role="SHOPKEEPER"
        )

    def test_create_shopkeeper_profile(self):
        """Test creating a shopkeeper profile"""
        profile = ShopkeeperProfile.objects.create(
            user=self.user, shop_name="Test Shop", shop_address="123 Test St"
        )
        self.assertEqual(profile.shop_name, "Test Shop")
        self.assertEqual(profile.user, self.user)
        self.assertFalse(profile.is_verified)


class AuthenticationAPITest(TestCase):
    """Test cases for authentication API endpoints"""

    @patch("core.services.SupabaseService.send_otp")
    def test_send_otp(self, mock_send_otp):
        """Test sending OTP"""
        mock_send_otp.return_value = {"success": True}

        from rest_framework.test import APIClient

        client = APIClient()

        response = client.post(
            "/api/accounts/auth/send-otp/",
            {"phone_number": "+1234567890"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_send_otp.called)

    def test_send_otp_invalid_format(self):
        """Test sending OTP with invalid phone format"""
        from rest_framework.test import APIClient

        client = APIClient()

        response = client.post(
            "/api/accounts/auth/send-otp/",
            {
                "phone_number": "1234567890"  # Missing +
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    @patch("core.services.SupabaseService.verify_otp")
    def test_verify_otp(self, mock_verify_otp):
        """Test verifying OTP"""
        # Mock Supabase response
        mock_response = MagicMock()
        mock_response.user.id = "supabase-user-id"
        mock_response.session.access_token = "access_token"
        mock_response.session.refresh_token = "refresh_token"
        mock_response.session.expires_in = 36000
        mock_response.session.expires_at = 1698432000
        mock_response.session.token_type = "bearer"

        mock_verify_otp.return_value = mock_response

        from rest_framework.test import APIClient

        client = APIClient()

        response = client.post(
            "/api/accounts/auth/verify-otp/",
            {"phone_number": "+1234567890", "otp": "123456"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.data)
        self.assertIn("user", response.data)
