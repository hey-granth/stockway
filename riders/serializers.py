from rest_framework import serializers
from .models import RiderProfile


class RiderProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the RiderProfile model.
    """

    class Meta:
        model = RiderProfile
        fields = ["warehouse", "payment_info"]
