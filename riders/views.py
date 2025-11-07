from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Prefetch
from django.db import transaction
from .models import RiderProfile
from .serializers import RiderProfileSerializer
from core.permissions import IsRider
from orders.models import Order, OrderItem
from orders.serializers import OrderSerializer, OrderStatusUpdateSerializer
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
    GET /api/rider/orders/
    List all orders assigned to the authenticated rider
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsRider]

    def get_queryset(self):
        # Get orders assigned to this rider through delivery
        return (
            Order.objects.filter(delivery__rider=self.request.user)
            .select_related("shopkeeper", "warehouse", "delivery", "delivery__rider")
            .prefetch_related(
                Prefetch(
                    "order_items", queryset=OrderItem.objects.select_related("item")
                )
            )
            .order_by("-created_at")
        )


class RiderOrderUpdateView(APIView):
    """
    PATCH /api/rider/orders/<int:pk>/
    Update order status (in_transit → delivered) for assigned orders
    """

    permission_classes = [IsAuthenticated, IsRider]

    def patch(self, request, pk):
        try:
            # Get order assigned to this rider
            order = Order.objects.select_related(
                "delivery", "delivery__rider", "shopkeeper", "warehouse"
            ).get(id=pk, delivery__rider=request.user)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found or not assigned to you"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Validate status update
        serializer = OrderStatusUpdateSerializer(
            data=request.data, context={"order": order}
        )

        if serializer.is_valid():
            new_status = serializer.validated_data["status"]

            with transaction.atomic():
                # Update order status
                order.status = new_status
                order.save(update_fields=["status", "updated_at"])

                # Update delivery status
                order.delivery.status = new_status
                order.delivery.save(update_fields=["status", "updated_at"])

            # Fetch updated order with full details
            order = (
                Order.objects.select_related(
                    "shopkeeper", "warehouse", "delivery", "delivery__rider"
                )
                .prefetch_related(
                    Prefetch(
                        "order_items", queryset=OrderItem.objects.select_related("item")
                    )
                )
                .get(id=order.id)
            )

            response_serializer = OrderSerializer(order)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
