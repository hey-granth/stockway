from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import RiderProfile
from .serializers import RiderProfileSerializer
from configs.permissions import IsRider


class RiderProfileView(APIView):
    """
    View for Rider to create or update their profile.
    """

    permission_classes = [IsAuthenticated, IsRider]

    def get(self, request):
        try:
            profile = RiderProfile.objects.get(user=request.user)
            serializer = RiderProfileSerializer(profile)
            return Response(serializer.data)
        except RiderProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request):
        serializer = RiderProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        try:
            profile = RiderProfile.objects.get(user=request.user)
        except RiderProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = RiderProfileSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)