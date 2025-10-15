from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .serializers import WarehouseSerializer
from inventory.serializers import ItemSerializer
from configs.permissions import IsWarehouseAdmin


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