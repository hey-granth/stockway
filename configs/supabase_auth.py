"""
Supabase Authentication Backend for Django REST Framework

This module provides JWT-based authentication using Supabase Auth.
It verifies Supabase JWT tokens and links them to Django User model via supabase_uid.
"""

import jwt
from rest_framework import authentication, exceptions
from django.contrib.auth import get_user_model
from configs.config import Config


User = get_user_model()


class SupabaseAuthentication(authentication.BaseAuthentication):
    """
    Custom DRF authentication class that verifies Supabase JWT tokens.

    Usage:
    - Add 'Authorization: Bearer <supabase_jwt>' header to requests
    - Token is verified using SUPABASE_JWT_SECRET
    - User is fetched/created based on supabase_uid from token payload
    """

    keyword: str = "Bearer"

    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if not auth_header:
            return None

        try:
            auth_parts = auth_header.split()

            if len(auth_parts) != 2:
                return None

            if auth_parts[0].lower() != self.keyword.lower():
                return None

            token = auth_parts[1]

        except (ValueError, UnicodeDecodeError):
            raise exceptions.AuthenticationFailed("Invalid token header")

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, token):
        """
        Verify the Supabase JWT token and return the associated user.
        """
        if not Config.SUPABASE_JWT_SECRET:
            raise exceptions.AuthenticationFailed("Supabase JWT secret not configured")

        try:
            # Decode and verify the JWT token
            payload = jwt.decode(
                token,
                Config.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
            )

        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token has expired")

        except jwt.InvalidTokenError as e:
            raise exceptions.AuthenticationFailed(f"Invalid token: {str(e)}")

        # Extract Supabase user ID from token
        supabase_uid: str = payload.get("sub")

        if not supabase_uid:
            raise exceptions.AuthenticationFailed("Token payload missing user ID")

        # Get or create Django user linked to Supabase UID
        try:
            user = User.objects.get(supabase_uid=supabase_uid)
        except User.DoesNotExist:
            # Auto-create user from Supabase token data
            user: User = self.create_user_from_token(payload)

        if not user.is_active:
            raise exceptions.AuthenticationFailed("User account is disabled")

        return (user, token)  # NOQA

    def create_user_from_token(self, payload) -> User:
        """
        Create a Django user from Supabase token payload.

        This is called when a valid Supabase user doesn't exist in Django yet.
        """
        supabase_uid: str = payload.get("sub")
        email: str = payload.get("email", "")
        phone: str = payload.get("phone", "")

        # Use phone or email as identifier
        phone_number: str = phone or email or f"user_{supabase_uid[:8]}"

        user: User = User.objects.create(
            supabase_uid=supabase_uid,
            phone_number=phone_number,
            email=email if email else "",
            is_verified=True,  # Already verified by Supabase
            is_active=True,
        )

        return user

    def authenticate_header(self, request) -> str:
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response.
        """
        return self.keyword


class SupabaseTokenAuthentication(authentication.TokenAuthentication):
    """
    Fallback authentication for legacy token-based auth.
    Allows gradual migration from Django tokens to Supabase JWT.
    """

    keyword: str = "Token"
