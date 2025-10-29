from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.auth import get_user_model
from accounts.models import ShopkeeperProfile

User = get_user_model()


class SendOTPSerializer(serializers.Serializer):
    """Serializer for sending OTP to phone number"""

    phone_number = serializers.CharField(
        max_length=20,
        required=True,
        help_text="Phone number in E.164 format (e.g., +1234567890)",
    )

    def validate_phone_number(self, value):
        """Validate phone number format"""
        # Basic validation - should start with +
        if not value.startswith("+"):
            raise serializers.ValidationError(
                "Phone number must be in E.164 format (e.g., +1234567890)"
            )
        # Remove + and check if remaining is digits
        if not value[1:].isdigit():
            raise serializers.ValidationError(
                "Phone number must contain only digits after +"
            )
        return value


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP"""

    phone_number = serializers.CharField(
        max_length=20, required=True, help_text="Phone number in E.164 format"
    )
    otp = serializers.CharField(
        max_length=6, required=True, help_text="6-digit OTP received via SMS"
    )

    def validate_phone_number(self, value):
        """Validate phone number format"""
        if not value.startswith("+"):
            raise serializers.ValidationError(
                "Phone number must be in E.164 format (e.g., +1234567890)"
            )
        if not value[1:].isdigit():
            raise serializers.ValidationError(
                "Phone number must contain only digits after +"
            )
        return value

    def validate_otp(self, value):
        """Validate OTP format"""
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits")
        return value


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""

    class Meta:
        model = User
        fields = [
            "id",
            "phone_number",
            "email",
            "full_name",
            "role",
            "is_active",
            "date_joined",
            "last_login",
        ]
        read_only_fields = ["id", "date_joined", "last_login"]


class ShopkeeperProfileSerializer(serializers.ModelSerializer):
    """Serializer for Shopkeeper Profile"""

    user = UserSerializer(read_only=True)
    latitude = serializers.FloatField(write_only=True, required=False, allow_null=True)
    longitude = serializers.FloatField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = ShopkeeperProfile
        fields = [
            "id",
            "user",
            "shop_name",
            "shop_address",
            "location",
            "latitude",
            "longitude",
            "gst_number",
            "is_verified",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "is_verified", "location"]

    def create(self, validated_data):
        from django.contrib.gis.geos import Point

        latitude = validated_data.pop("latitude", None)
        longitude = validated_data.pop("longitude", None)

        if latitude is not None and longitude is not None:
            validated_data["location"] = Point(longitude, latitude, srid=4326)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        from django.contrib.gis.geos import Point

        latitude = validated_data.pop("latitude", None)
        longitude = validated_data.pop("longitude", None)

        if latitude is not None and longitude is not None:
            validated_data["location"] = Point(longitude, latitude, srid=4326)

        return super().update(instance, validated_data)
