from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from django.conf import settings
import jwt
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

User = get_user_model()


class SupabaseAuthentication(BaseAuthentication):
    """
    Enhanced Supabase JWT authentication with comprehensive validation
    """

    def authenticate(self, request):
        """
        Authenticate the request using Supabase JWT token with full validation

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
                self._log_auth_failure(request, "Invalid header format")
                raise AuthenticationFailed("Invalid authorization header format")

            access_token = parts[1]

            # Verify and decode JWT token
            payload = self._verify_jwt_token(access_token)

            if not payload:
                self._log_auth_failure(request, "Token verification failed")
                raise AuthenticationFailed("Invalid or expired token")

            # Extract user ID from payload
            supabase_uid = payload.get("sub")
            if not supabase_uid:
                self._log_auth_failure(request, "Missing subject in token")
                raise AuthenticationFailed("Invalid token payload")

            # Get or create Django user
            user = self._get_or_create_user(payload)

            if not user.is_active:
                self._log_auth_failure(request, f"Inactive user: {user.id}")
                raise AuthenticationFailed("User account is disabled")

            return (user, access_token)

        except jwt.ExpiredSignatureError:
            self._log_auth_failure(request, "Token expired")
            raise AuthenticationFailed("Token has expired")
        except jwt.InvalidTokenError as e:
            self._log_auth_failure(request, f"Invalid token: {str(e)}")
            raise AuthenticationFailed("Invalid token")
        except AuthenticationFailed:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}", exc_info=True)
            self._log_auth_failure(request, f"Unexpected error: {str(e)}")
            raise AuthenticationFailed("Authentication failed")

    def _verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token signature, expiry, issuer, and audience

        Args:
            token: JWT token string

        Returns:
            Decoded payload or None
        """
        try:
            jwt_secret = settings.SUPABASE_JWT_SECRET
            supabase_url = settings.SUPABASE_URL

            if not jwt_secret:
                logger.error("SUPABASE_JWT_SECRET not configured")
                return None

            # Decode and verify token
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": False,  # Supabase doesn't always include aud
                    "require_exp": True,
                },
            )

            # Verify issuer matches Supabase project
            iss = payload.get("iss")
            if iss and supabase_url:
                expected_issuer = f"{supabase_url}/auth/v1"
                if iss != expected_issuer:
                    logger.warning(
                        f"Token issuer mismatch. Expected: {expected_issuer}, Got: {iss}"
                    )
                    return None

            # Verify token type
            token_type = payload.get("token_type")
            if token_type and token_type != "bearer":
                logger.warning(f"Invalid token type: {token_type}")
                return None

            return payload

        except jwt.ExpiredSignatureError:
            raise
        except jwt.InvalidTokenError:
            raise
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}", exc_info=True)
            return None

    def _get_or_create_user(self, payload: Dict[str, Any]) -> User:
        """
        Get or create Django user from JWT payload

        Args:
            payload: Decoded JWT payload

        Returns:
            User instance
        """
        supabase_uid = payload.get("sub")
        email = payload.get("email")
        phone = payload.get("phone")

        try:
            # Try to find user by supabase_uid (indexed field)
            user = User.objects.get(supabase_uid=supabase_uid)
            logger.debug(f"Found existing user: {supabase_uid}")
        except User.DoesNotExist:
            # Prevent user creation without email or phone
            if not email and not phone:
                logger.error(
                    f"Cannot create user without email or phone: {supabase_uid}"
                )
                raise AuthenticationFailed("Invalid user credentials")

            # Create new user with validated data
            user = User.objects.create(
                email=email if email else f"{supabase_uid}@placeholder.local",
                phone_number=phone,
                supabase_uid=supabase_uid,
                is_active=True,
            )
            logger.info(f"Created new user: {supabase_uid}, email: {email or 'N/A'}")

        return user

    def _log_auth_failure(self, request, reason: str):
        """
        Log authentication failures for security monitoring

        Args:
            request: HTTP request object
            reason: Failure reason
        """
        ip_address = self._get_client_ip(request)
        logger.warning(
            f"Authentication failed - IP: {ip_address}, Reason: {reason}",
            extra={
                "ip_address": ip_address,
                "path": request.path,
                "method": request.method,
                "reason": reason,
            },
        )

    def _get_client_ip(self, request) -> str:
        """
        Get client IP address from request

        Args:
            request: HTTP request object

        Returns:
            IP address string
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "unknown")
        return ip
