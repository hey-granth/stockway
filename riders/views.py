
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import RiderProfile
from .serializers import RiderProfileSerializer
from configs.permissions import IsRider
from orders.models import Order
from orders.serializers import OrderSerializer
from delivery.models import Delivery


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


class RiderOrderListView(generics.ListAPIView):
    """
    API view for riders to list their assigned orders.
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsRider]

    def get_queryset(self):
        return Order.objects.filter(delivery__rider=self.request.user)


class RiderOrderDeliverView(APIView):
    """
    API view for riders to mark an order as delivered.
    """

    permission_classes = [IsAuthenticated, IsRider]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, delivery__rider=request.user)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found."},
                status=status.HTTP_44_NOT_FOUND,
            )

        if order.status != "in_transit":
            return Response(
                {"error": "Order cannot be delivered."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = "delivered"
        order.save()

        delivery = Delivery.objects.get(order=order)
        delivery.status = "delivered"
        delivery.save()

        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)