from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from core.services import SupabaseService
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class SupabaseAuthentication(BaseAuthentication):
    """
    Custom authentication class for Supabase JWT tokens
    """

    def authenticate(self, request):
        """
        Authenticate the request using Supabase access token

        Returns:
            tuple: (user, token) or None
        """
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None

        try:
            # Extract token from "Bearer <token>"
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                raise AuthenticationFailed("Invalid authorization header format")

            access_token = parts[1]

            # Verify token with Supabase
            supabase_user = SupabaseService.get_user(access_token)

            # Access user data from response
            user_data = (
                supabase_user.user
                if hasattr(supabase_user, "user")
                else supabase_user.get("user")
            )

            if not user_data:
                raise AuthenticationFailed("Invalid token")

            # Get or create Django user
            user = self._get_or_create_user(user_data)

            return (user, access_token)

        except AuthenticationFailed:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise AuthenticationFailed("Authentication failed")

    def _get_or_create_user(self, supabase_user):
        """
        Get or create Django user from Supabase user data
        """
        supabase_uid = (
            supabase_user.id
            if hasattr(supabase_user, "id")
            else supabase_user.get("id")
        )
        phone = (
            supabase_user.phone
            if hasattr(supabase_user, "phone")
            else supabase_user.get("phone")
        )

        try:
            # Try to find user by supabase_uid
            user = User.objects.get(supabase_uid=supabase_uid)
        except User.DoesNotExist:
            # Create new user
            user = User.objects.create(
                phone_number=phone, supabase_uid=supabase_uid, is_active=True
            )
            logger.info(f"Created new user for phone: {phone}")

        return user
