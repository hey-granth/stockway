from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from .models import Notification
from .serializers import NotificationSerializer, MarkAsReadSerializer


class NotificationPagination(PageNumberPagination):
    """Custom pagination for notifications"""
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class NotificationListView(APIView):
    """
    GET /notifications/
    List authenticated user's notifications, unread first, paginated
    """
    permission_classes = [IsAuthenticated]
    pagination_class = NotificationPagination

    def get(self, request):
        """Get user's notifications with unread first"""
        user = request.user

        # Get notifications ordered by read status (unread first) and creation date
        notifications = Notification.objects.filter(user=user).order_by("is_read", "-created_at")

        # Apply pagination
        paginator = self.pagination_class()
        paginated_notifications = paginator.paginate_queryset(notifications, request)

        serializer = NotificationSerializer(paginated_notifications, many=True)
        return paginator.get_paginated_response(serializer.data)


class MarkNotificationReadView(APIView):
    """
    PATCH /notifications/read/
    Mark one or all notifications as read
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        """Mark notification(s) as read"""
        user = request.user
        serializer = MarkAsReadSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        validated_data = serializer.validated_data

        if validated_data.get("mark_all"):
            # Mark all user's notifications as read
            updated_count = Notification.objects.filter(
                user=user,
                is_read=False
            ).update(is_read=True)

            return Response(
                {
                    "success": True,
                    "message": f"Marked {updated_count} notifications as read"
                },
                status=status.HTTP_200_OK
            )
        else:
            # Mark specific notification as read
            notification_id = validated_data.get("notification_id")

            try:
                notification = Notification.objects.get(
                    id=notification_id,
                    user=user
                )
                notification.is_read = True
                notification.save()

                return Response(
                    {
                        "success": True,
                        "message": "Notification marked as read",
                        "notification": NotificationSerializer(notification).data
                    },
                    status=status.HTTP_200_OK
                )
            except Notification.DoesNotExist:
                return Response(
                    {"error": "Notification not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

