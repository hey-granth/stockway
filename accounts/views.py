import random
import requests
from django.core.cache import cache
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User
from .serializers import UserSerializer, OTPVerifySerializer, OTPRequestSerializer
from configs.config import Config


class RequestOTP(APIView):
    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data["phone_number"]

            try:
                user = User.objects.get(phone_number=phone_number)
            except User.DoesNotExist:
                user = User.objects.create(phone_number=phone_number)

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

            try:
                user = User.objects.get(phone_number=phone_number)
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
                )

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
