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
    Serializer for the ShopkeeperProfile model with full onboarding fields.
    """
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = ShopkeeperProfile
        fields = [
            'id',
            'user_phone',
            'user_email',
            'shop_name',
            'address',
            'latitude',
            'longitude',
            'gst_number',
            'license_number',
            'onboarding_completed',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'onboarding_completed', 'created_at', 'updated_at']

    def validate(self, data):
        """
        Validate that at least one of gst_number or license_number is provided.
        """
        gst_number = data.get('gst_number', self.instance.gst_number if self.instance else None)
        license_number = data.get('license_number', self.instance.license_number if self.instance else None)

        # If both are provided or being updated, at least one must be non-empty
        if 'gst_number' in data or 'license_number' in data:
            if not gst_number and not license_number:
                raise serializers.ValidationError(
                    "At least one of 'gst_number' or 'license_number' must be provided."
                )

        return data

    def validate_latitude(self, value):
        """Validate latitude is within valid range."""
        if value is not None and (value < -90 or value > 90):
            raise serializers.ValidationError("Latitude must be between -90 and 90.")
        return value

    def validate_longitude(self, value):
        """Validate longitude is within valid range."""
        if value is not None and (value < -180 or value > 180):
            raise serializers.ValidationError("Longitude must be between -180 and 180.")
        return value

    def update(self, instance, validated_data):
        """
        Update profile and automatically mark onboarding as complete if all fields are filled.
        """
        # Update all fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Check and update onboarding status
        instance.mark_onboarding_complete()
        instance.save()

        return instance
