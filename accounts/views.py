import random
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import UserSerializer, VerifyOTPSerializer


class RequestOTP(APIView):
    def post(self, request):
        phone_number = request.data.get("phone_number")
        if not phone_number:
            return Response(
                {"error": "Phone number is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            # For simplicity, creating a user if not found.
            # In a real-world scenario, you might want a separate registration flow.
            user = User.objects.create(phone_number=phone_number)

        otp = str(random.randint(100000, 999999))
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save()

        # In a real application, you would send the OTP via SMS.
        print(f"OTP for {phone_number}: {otp}")

        return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)


class VerifyOTP(APIView):
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data["phone_number"]
            otp = serializer.validated_data["otp"]

            try:
                user = User.objects.get(phone_number=phone_number)
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
                )

            if user.otp != otp:
                return Response(
                    {"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST
                )

            if timezone.now() > user.otp_created_at + timedelta(minutes=5):
                return Response(
                    {"error": "OTP has expired"}, status=status.HTTP_400_BAD_REQUEST
                )

            user.is_verified = True
            user.otp = None  # Clear OTP after verification
            user.otp_created_at = None
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
