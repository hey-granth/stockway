
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Order
from .serializers import OrderCreateSerializer, OrderSerializer
from configs.permissions import IsShopkeeper


class ShopkeeperOrderCreateAPIView(generics.CreateAPIView):
    """
    API view for shopkeepers to create a new order.
    """

    serializer_class = OrderCreateSerializer
    permission_classes = [IsAuthenticated, IsShopkeeper]

    def get_serializer_context(self):
        return {"request": self.request}


class ShopkeeperOrderListAPIView(generics.ListAPIView):
    """
    API view for shopkeepers to list their orders.
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsShopkeeper]

    def get_queryset(self):
        return Order.objects.filter(shopkeeper=self.request.user)

