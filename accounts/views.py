from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from core.services import SupabaseService
from accounts.serializers import (
    SendOTPSerializer,
    VerifyOTPSerializer,
    UserSerializer,
)
import logging


logger = logging.getLogger(__name__)

User = get_user_model()


class SendOTPView(APIView):
    """
    Send OTP to email for authentication
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """
        Send OTP to the provided email

        Request body:
        {
            "email": "user@example.com"
        }
        """
        serializer = SendOTPSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data["email"]

        try:
            logger.info(f"OTP send request received for email: {email}")
            result = SupabaseService.send_otp(email)
            return Response(
                {
                    "success": True,
                    "message": "OTP sent successfully to your email",
                    "email": email,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Failed to send OTP: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyOTPView(APIView):
    """
    Verify OTP and authenticate user
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """
        Verify OTP and return authentication tokens

        Request body:
        {
            "email": "user@example.com",
            "otp": "123456"
        }
        """
        serializer = VerifyOTPSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        try:
            logger.info(f"Attempting OTP verification for email: {email}")

            # Verify OTP with Supabase
            supabase_response = SupabaseService.verify_otp(email, otp)

            # Access user data from response
            user_data = (
                supabase_response.user
                if hasattr(supabase_response, "user")
                else supabase_response.get("user")
            )
            session_data = (
                supabase_response.session
                if hasattr(supabase_response, "session")
                else supabase_response.get("session")
            )

            if not user_data:
                return Response(
                    {"error": "Invalid OTP"}, status=status.HTTP_401_UNAUTHORIZED
                )

            # Get or create Django user
            user_id = user_data.id if hasattr(user_data, "id") else user_data.get("id")
            user, created = User.objects.get_or_create(
                supabase_uid=user_id,
                defaults={"email": email, "is_active": True},
            )

            if created:
                logger.info(f"New user created during OTP verification: {email}")
            else:
                logger.debug(f"Existing user authenticated: {email}")

            # Prepare response
            response_data = {
                "access_token": session_data.access_token
                if hasattr(session_data, "access_token")
                else session_data.get("access_token"),
                "refresh_token": session_data.refresh_token
                if hasattr(session_data, "refresh_token")
                else session_data.get("refresh_token"),
                "expires_in": session_data.expires_in
                if hasattr(session_data, "expires_in")
                else session_data.get("expires_in"),
                "expires_at": session_data.expires_at
                if hasattr(session_data, "expires_at")
                else session_data.get("expires_at"),
                "token_type": session_data.token_type
                if hasattr(session_data, "token_type")
                else session_data.get("token_type"),
                "user": UserSerializer(user).data,
            }

            logger.info(
                f"OTP verification successful for user: {email}, user_id: {user.id}"
            )
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"OTP verification failed: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    """
    Logout user by invalidating Supabase session
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Logout the authenticated user
        """
        try:
            # Get access token from request
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                access_token = auth_header.split(" ")[1]
                SupabaseService.sign_out(access_token)

            return Response(
                {"success": True, "message": "Logged out successfully"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CurrentUserView(APIView):
    """
    Get current authenticated user details
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get current user information
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
