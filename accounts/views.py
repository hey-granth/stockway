import random
import requests
from django.core.cache import cache
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import User, ShopkeeperProfile
from .serializers import (
    UserSerializer,
    OTPVerifySerializer,
    OTPRequestSerializer,
    ShopkeeperProfileSerializer,
)
from configs.config import Config
from configs.permissions import IsShopkeeper


class RequestOTP(APIView):
    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data["phone_number"]

            otp = str(random.randint(100000, 999999))
            cache.set(f"otp:{phone_number}", otp, timeout=300)  # 5 minutes

            # Send OTP via Fast2SMS
            url = "https://www.fast2sms.com/dev/bulkV2"
            payload = {
                "message": f"Your OTP is {otp}",
                "language": "english",
                "route": "q",
                "numbers": phone_number,
            }
            headers = {"authorization": Config.FAST2SMS_API_KEY}
            try:
                response = requests.post(url, data=payload, headers=headers)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                return Response(
                    {"error": f"Failed to send OTP: {e}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(
                {"message": "OTP sent successfully"}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTP(APIView):
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data["phone_number"]
            otp = serializer.validated_data["otp"]

            stored_otp = cache.get(f"otp:{phone_number}")

            if not stored_otp:
                return Response(
                    {"error": "OTP has expired or does not exist"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if stored_otp != otp:
                return Response(
                    {"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST
                )

            cache.delete(f"otp:{phone_number}")

            user, created = User.objects.get_or_create(phone_number=phone_number)

            if not user.is_verified:
                user.is_verified = True
                user.save()

            token, _ = Token.objects.get_or_create(user=user)

            return Response(
                {
                    "message": "OTP verified successfully",
                    "token": token.key,
                    "user": UserSerializer(user).data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShopkeeperProfileView(APIView):
    """
    View for Shopkeeper to create or update their profile.
    """

    permission_classes = [IsAuthenticated, IsShopkeeper]

    def get(self, request):
        try:
            profile = ShopkeeperProfile.objects.get(user=request.user)
            serializer = ShopkeeperProfileSerializer(profile)
            return Response(serializer.data)
        except ShopkeeperProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request):
        serializer = ShopkeeperProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        try:
            profile = ShopkeeperProfile.objects.get(user=request.user)
        except ShopkeeperProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = ShopkeeperProfileSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerProfileUpdateView(APIView):
    """
    PATCH /api/customers/profile/

    Update customer (shopkeeper) profile with onboarding completion.
    Only authenticated shopkeepers can access this endpoint.
    Automatically marks onboarding_completed=True when all required fields are filled.
    """

    permission_classes = [IsAuthenticated, IsShopkeeper]

    def get(self, request):
        """
        Get the current user's profile.

        Returns:
            200: Profile data
            404: Profile not found (create one first)
        """
        try:
            profile = ShopkeeperProfile.objects.get(user=request.user)
            serializer = ShopkeeperProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ShopkeeperProfile.DoesNotExist:
            return Response(
                {
                    "error": "Profile not found. Please create your profile first.",
                    "detail": "Use POST method to create a new profile.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

    def post(self, request):
        """
        Create a new profile for the authenticated shopkeeper.

        Returns:
            201: Profile created successfully
            400: Validation errors
            409: Profile already exists
        """
        # Check if profile already exists
        if ShopkeeperProfile.objects.filter(user=request.user).exists():
            return Response(
                {
                    "error": "Profile already exists. Use PATCH to update.",
                    "detail": "A profile is already associated with this user.",
                },
                status=status.HTTP_409_CONFLICT,
            )

        serializer = ShopkeeperProfileSerializer(data=request.data)
        if serializer.is_valid():
            profile = serializer.save(user=request.user)
            return Response(
                ShopkeeperProfileSerializer(profile).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        """
        Partially update the customer profile.

        Accepts partial data and updates only the provided fields.
        Automatically sets onboarding_completed=True when all required fields are present:
        - shop_name
        - address
        - latitude
        - longitude
        - At least one of: gst_number or license_number

        Returns:
            200: Profile updated successfully
            404: Profile not found
            400: Validation errors
        """
        try:
            profile = ShopkeeperProfile.objects.get(user=request.user)
        except ShopkeeperProfile.DoesNotExist:
            return Response(
                {
                    "error": "Profile not found. Please create your profile first.",
                    "detail": "Use POST method to create a new profile.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Partial update
        serializer = ShopkeeperProfileSerializer(
            profile, data=request.data, partial=True  # Allow partial updates
        )

        if serializer.is_valid():
            updated_profile = serializer.save()
            return Response(
                ShopkeeperProfileSerializer(updated_profile).data,
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """
        Fully replace the customer profile (all fields required).

        Returns:
            200: Profile updated successfully
            404: Profile not found
            400: Validation errors
        """
        try:
            profile = ShopkeeperProfile.objects.get(user=request.user)
        except ShopkeeperProfile.DoesNotExist:
            return Response(
                {
                    "error": "Profile not found. Please create your profile first.",
                    "detail": "Use POST method to create a new profile.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ShopkeeperProfileSerializer(profile, data=request.data)

        if serializer.is_valid():
            updated_profile = serializer.save()
            return Response(
                ShopkeeperProfileSerializer(updated_profile).data,
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

