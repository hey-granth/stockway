"""
Test cases for email-based OTP authentication using Supabase

These tests verify the complete authentication flow:
1. Send OTP to email
2. Verify OTP and get session tokens
3. Use tokens to authenticate requests
4. Logout
"""

from django.test import TestCase
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailOTPAuthenticationTest(TestCase):
    """Test email-based OTP authentication flow"""

    def setUp(self):
        """Set up test client"""
        self.client = APIClient()
        self.email = "test@example.com"
        self.otp = "123456"

    @patch("core.services.SupabaseService.send_otp")
    def test_send_otp_success(self, mock_send_otp):
        """Test sending OTP to email successfully"""
        # Mock Supabase response
        mock_send_otp.return_value = {
            "success": True,
            "message": "OTP sent successfully",
        }

        # Send request
        response = self.client.post(
            "/api/accounts/send-otp/", {"email": self.email}, format="json"
        )

        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["email"], self.email)
        mock_send_otp.assert_called_once_with(self.email)

    def test_send_otp_invalid_email(self):
        """Test sending OTP with invalid email format"""
        response = self.client.post(
            "/api/accounts/send-otp/", {"email": "invalid-email"}, format="json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)

    @patch("core.services.SupabaseService.verify_otp")
    def test_verify_otp_success(self, mock_verify_otp):
        """Test verifying OTP successfully and getting tokens"""
        # Mock Supabase user data
        mock_user_data = MagicMock()
        mock_user_data.id = "supabase-user-123"
        mock_user_data.email = self.email

        # Mock Supabase session data
        mock_session_data = MagicMock()
        mock_session_data.access_token = "mock-access-token"
        mock_session_data.refresh_token = "mock-refresh-token"
        mock_session_data.expires_in = 36000
        mock_session_data.expires_at = 1698432000
        mock_session_data.token_type = "bearer"

        # Mock Supabase response
        mock_response = MagicMock()
        mock_response.user = mock_user_data
        mock_response.session = mock_session_data
        mock_verify_otp.return_value = mock_response

        # Send request
        response = self.client.post(
            "/api/accounts/verify-otp/",
            {"email": self.email, "otp": self.otp},
            format="json",
        )

        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], self.email)

        # Verify user was created in Django database
        user = User.objects.get(email=self.email)
        self.assertEqual(user.supabase_uid, "supabase-user-123")
        self.assertTrue(user.is_active)

    def test_verify_otp_invalid_format(self):
        """Test verifying OTP with invalid format"""
        response = self.client.post(
            "/api/accounts/verify-otp/",
            {
                "email": self.email,
                "otp": "abc123",  # Invalid - should be digits only
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)

    @patch("core.services.SupabaseService.verify_otp")
    def test_verify_otp_invalid_token(self, mock_verify_otp):
        """Test verifying with invalid OTP token"""
        # Mock Supabase error
        mock_verify_otp.side_effect = Exception("Invalid or expired OTP")

        response = self.client.post(
            "/api/accounts/verify-otp/",
            {"email": self.email, "otp": self.otp},
            format="json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.data)

    @patch("core.services.SupabaseService.get_user")
    def test_authenticated_request(self, mock_get_user):
        """Test making authenticated request with access token"""
        # Create a test user
        user = User.objects.create(
            email=self.email, supabase_uid="supabase-user-123", is_active=True
        )

        # Mock Supabase user verification
        mock_user_data = MagicMock()
        mock_user_data.id = "supabase-user-123"
        mock_user_data.email = self.email

        mock_response = MagicMock()
        mock_response.user = mock_user_data
        mock_get_user.return_value = mock_response

        # Make authenticated request
        self.client.credentials(HTTP_AUTHORIZATION="Bearer mock-access-token")
        response = self.client.get("/api/accounts/me/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], self.email)

    @patch("core.services.SupabaseService.sign_out")
    @patch("core.services.SupabaseService.get_user")
    def test_logout(self, mock_get_user, mock_sign_out):
        """Test logout functionality"""
        # Create a test user
        user = User.objects.create(
            email=self.email, supabase_uid="supabase-user-123", is_active=True
        )

        # Mock Supabase user verification
        mock_user_data = MagicMock()
        mock_user_data.id = "supabase-user-123"
        mock_user_data.email = self.email

        mock_response = MagicMock()
        mock_response.user = mock_user_data
        mock_get_user.return_value = mock_response

        # Mock sign out
        mock_sign_out.return_value = {
            "success": True,
            "message": "Signed out successfully",
        }

        # Make logout request
        self.client.credentials(HTTP_AUTHORIZATION="Bearer mock-access-token")
        response = self.client.post("/api/accounts/logout/")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        mock_sign_out.assert_called_once()


class BackwardCompatibilityTest(TestCase):
    """Test backward compatibility with existing API clients"""

    def setUp(self):
        """Set up test client"""
        self.client = APIClient()

    @patch("core.services.SupabaseService.verify_otp")
    def test_response_schema_unchanged(self, mock_verify_otp):
        """Verify response schema remains identical for backward compatibility"""
        # Mock Supabase response
        mock_user_data = MagicMock()
        mock_user_data.id = "supabase-user-123"
        mock_user_data.email = "test@example.com"

        mock_session_data = MagicMock()
        mock_session_data.access_token = "mock-access-token"
        mock_session_data.refresh_token = "mock-refresh-token"
        mock_session_data.expires_in = 36000
        mock_session_data.expires_at = 1698432000
        mock_session_data.token_type = "bearer"

        mock_response = MagicMock()
        mock_response.user = mock_user_data
        mock_response.session = mock_session_data
        mock_verify_otp.return_value = mock_response

        # Send request
        response = self.client.post(
            "/api/accounts/verify-otp/",
            {"email": "test@example.com", "otp": "123456"},
            format="json",
        )

        # Verify required fields are present
        required_fields = [
            "access_token",
            "refresh_token",
            "expires_in",
            "expires_at",
            "token_type",
            "user",
        ]

        for field in required_fields:
            self.assertIn(
                field, response.data, f"Required field '{field}' missing from response"
            )

        # Verify user object structure
        user_fields = ["id", "email", "role", "is_active"]
        for field in user_fields:
            self.assertIn(
                field, response.data["user"], f"Required user field '{field}' missing"
            )
