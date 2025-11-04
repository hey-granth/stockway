from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.auth import get_user_model
from accounts.models import ShopkeeperProfile

User = get_user_model()


class SendOTPSerializer(serializers.Serializer):
    """Serializer for sending OTP to email"""

    email = serializers.EmailField(
        required=True,
        help_text="Email address to send OTP to",
    )

    def validate_email(self, value):
        """Validate email format"""
        # EmailField already validates format, just return
        return value.lower()


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP"""

    email = serializers.EmailField(required=True, help_text="Email address")
    otp = serializers.CharField(
        max_length=6, required=True, help_text="6-digit OTP received via email"
    )

    def validate_email(self, value):
        """Validate email format"""
        return value.lower()

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
