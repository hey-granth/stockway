from rest_framework import serializers
from .models import User, ShopkeeperProfile


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    """

    class Meta:
        model = User
        fields = [
            "id",
            "phone_number",
            "role",
            "is_verified",
            "first_name",
            "last_name",
        ]
        read_only_fields = ["id", "is_verified"]


class OTPRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting an OTP.
    """

    phone_number = serializers.CharField(max_length=15)


class OTPVerifySerializer(serializers.Serializer):
    """
    Serializer for verifying an OTP.
    """

    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)


class ShopkeeperProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the ShopkeeperProfile model.
    """

    class Meta:
        model = ShopkeeperProfile
        fields = ["shop_name", "latitude", "longitude"]
