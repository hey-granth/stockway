from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404

from .serializers import WarehouseSerializer
from inventory.serializers import ItemSerializer
from configs.permissions import IsWarehouseAdmin, IsSuperAdmin
from .models import Warehouse
from .permissions import IsWarehouseOwnerOrSuperAdmin, HasWarehouseRole
from orders.models import Order
from orders.serializers import OrderSerializer
from delivery.models import Delivery
from riders.models import RiderProfile
from accounts.models import User


class WarehouseOnboardingView(APIView):
    """
    View for Warehouse Admin to create a warehouse and add inventory.
    """

    permission_classes = [IsAuthenticated, IsWarehouseAdmin]

    def post(self, request):
        warehouse_data = request.data.get("warehouse")
        items_data = request.data.get("items")

        if not warehouse_data or not items_data:
            return Response(
                {"error": "Warehouse and items data are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        warehouse_serializer = WarehouseSerializer(data=warehouse_data)
        if warehouse_serializer.is_valid():
            warehouse = warehouse_serializer.save(admin=request.user)

            items = []
            for item_data in items_data:
                item_data["warehouse"] = warehouse.id
                item_serializer = ItemSerializer(data=item_data)
                if item_serializer.is_valid():
                    item_serializer.save()
                    items.append(item_serializer.data)
                else:
                    # If any item is invalid, delete the created warehouse and return errors
                    warehouse.delete()
                    return Response(
                        item_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )

            return Response(
                {
                    "warehouse": warehouse_serializer.data,
                    "items": items,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(warehouse_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WarehouseCreateView(APIView):
    """Create a warehouse. Only WAREHOUSE_ADMIN and SUPER_ADMIN.
    SUPER_ADMIN may specify an admin user via admin field; otherwise admin is request.user.
    """

    permission_classes = [IsAuthenticated, HasWarehouseRole]

    def post(self, request):
        data = request.data.copy()
        if not IsSuperAdmin().has_permission(request, self):
            # Force admin to be requester
            data.pop("admin", None)
        serializer = WarehouseSerializer(data=data)
        if serializer.is_valid():
            admin_user = (
                request.user
                if not IsSuperAdmin().has_permission(request, self)
                else serializer.validated_data.get("admin", request.user)
            )
            warehouse = serializer.save(admin=admin_user)
            return Response(
                WarehouseSerializer(warehouse).data, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WarehouseDetailView(APIView):
    """Retrieve or update a single warehouse."""

    permission_classes = [
        IsAuthenticated,
        HasWarehouseRole,
        IsWarehouseOwnerOrSuperAdmin,
    ]

    def get_object(self, pk):
        return get_object_or_404(Warehouse, pk=pk)

    def get(self, request, pk):
        warehouse = self.get_object(pk)
        # object-level permission
        for perm in self.permission_classes:
            if hasattr(perm(), "has_object_permission"):
                if not perm().has_object_permission(request, self, warehouse):
                    return Response(
                        {"detail": "Not found."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
        return Response(WarehouseSerializer(warehouse).data)

    # Both PATCH and PUT methods are supported for updates. PATCH allows partial updates (uses partial=True) in serializers, while PUT requires all fields.
    def patch(self, request, pk):
        warehouse = self.get_object(pk)
        for perm in self.permission_classes:
            if hasattr(perm(), "has_object_permission"):
                if not perm().has_object_permission(request, self, warehouse):
                    return Response(
                        {"detail": "Not found."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
        data = request.data.copy()
        if not IsSuperAdmin().has_permission(request, self):
            data.pop("admin", None)
        serializer = WarehouseSerializer(warehouse, data=data, partial=True)
        if serializer.is_valid():
            if "admin" in serializer.validated_data and not IsSuperAdmin().has_permission(
                request, self
            ):
                return Response(
                    {"admin": ["You cannot change admin."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        warehouse = self.get_object(pk)
        for perm in self.permission_classes:
            if hasattr(perm(), "has_object_permission"):
                if not perm().has_object_permission(request, self, warehouse):
                    return Response(
                        {"detail": "Not found."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
        data = request.data.copy()
        if not IsSuperAdmin().has_permission(request, self):
            data.pop("admin", None)
        serializer = WarehouseSerializer(warehouse, data=data)
        if serializer.is_valid():
            if "admin" in serializer.validated_data and not IsSuperAdmin().has_permission(
                request, self
            ):
                return Response(
                    {"admin": ["You cannot change admin."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WarehouseOrderListView(generics.ListAPIView):
    """
    API view for warehouse admins to list orders for their warehouse.
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsWarehouseAdmin]

    def get_queryset(self):
        warehouse_id = self.kwargs.get("warehouse_id")
        return Order.objects.filter(warehouse_id=warehouse_id)


class WarehouseOrderConfirmView(APIView):
    """
    API view for warehouse admins to confirm an order.
    """

    permission_classes = [IsAuthenticated, IsWarehouseAdmin]

    def post(self, request, warehouse_id, order_id):
        try:
            order = Order.objects.get(id=order_id, warehouse_id=warehouse_id)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if order.status != "pending":
            return Response(
                {"error": "Order cannot be confirmed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = "accepted"
        order.save()
        return Response(
            OrderSerializer(order).data, status=status.HTTP_200_OK
        )


class WarehouseOrderAssignView(APIView):
    """
    API view for warehouse admins to assign a rider to an order.
    """

    permission_classes = [IsAuthenticated, IsWarehouseAdmin]

    def post(self, request, warehouse_id, order_id):
        rider_id = request.data.get("rider_id")

        try:
            order = Order.objects.get(id=order_id, warehouse_id=warehouse_id)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if order.status != "accepted":
            return Response(
                {"error": "Order cannot be assigned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            rider_user = User.objects.get(id=rider_id, role=User.Role.RIDER)
            rider_profile = RiderProfile.objects.get(user=rider_user)
        except (User.DoesNotExist, RiderProfile.DoesNotExist):
            return Response(
                {"error": "Rider not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Haversine formula to calculate distance
        from math import radians, sin, cos, sqrt, atan2

        shopkeeper_profile = order.shopkeeper.shopkeeper_profile
        warehouse = order.warehouse

        lat1, lon1 = radians(shopkeeper_profile.latitude), radians(
            shopkeeper_profile.longitude
        )
        lat2, lon2 = radians(warehouse.latitude), radians(warehouse.longitude)

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = 6371 * c  # Radius of earth in kilometers

        # delivery fee is based on distance
        delivery_fee = distance * 10  # 10 per km

        delivery = Delivery.objects.create(
            order=order, rider=rider_user, delivery_fee=delivery_fee
        )

        order.status = "in_transit"
        order.save()

        return Response(
            OrderSerializer(order).data, status=status.HTTP_200_OK
        )
