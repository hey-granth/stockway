# Notification System API Documentation

## Overview
The notification system provides a complete pipeline for managing user notifications across Django, Celery, RabbitMQ, and Supabase.

## Architecture
- **Django**: REST API endpoints and database models
- **Celery**: Asynchronous task processing
- **RabbitMQ**: Message broker for task queue
- **Redis**: Result backend for Celery
- **Supabase Edge Functions**: Optional push/SMS delivery

## Endpoints

### 1. List Notifications
Get paginated list of authenticated user's notifications, with unread notifications first.

**Endpoint:** `GET /api/notifications/`

**Authentication:** Required

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20, max: 100)

**Response:**
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/notifications/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Order #123 Update",
      "message": "Your order status has been updated to: confirmed",
      "type": "order_update",
      "is_read": false,
      "created_at": "2025-01-01T12:00:00Z"
    },
    {
      "id": 2,
      "title": "Payment Update",
      "message": "Payment #456 of ₹1000 has been completed",
      "type": "payment",
      "is_read": true,
      "created_at": "2025-01-01T11:30:00Z"
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Authentication required

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/notifications/?page=1&page_size=20"
```

---

### 2. Mark Notification(s) as Read
Mark one or all notifications as read for the authenticated user.

**Endpoint:** `PATCH /api/notifications/read/`

**Authentication:** Required

**Request Body (Option 1 - Single notification):**
```json
{
  "notification_id": 1
}
```

**Request Body (Option 2 - All notifications):**
```json
{
  "mark_all": true
}
```

**Response (Single notification):**
```json
{
  "success": true,
  "message": "Notification marked as read",
  "notification": {
    "id": 1,
    "title": "Order #123 Update",
    "message": "Your order status has been updated to: confirmed",
    "type": "order_update",
    "is_read": true,
    "created_at": "2025-01-01T12:00:00Z"
  }
}
```

**Response (All notifications):**
```json
{
  "success": true,
  "message": "Marked 5 notifications as read"
}
```

**Status Codes:**
- `200 OK`: Success
- `400 Bad Request`: Invalid request body
- `401 Unauthorized`: Authentication required
- `404 Not Found`: Notification not found or doesn't belong to user

**Examples:**
```bash
# Mark single notification as read
curl -X PATCH \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notification_id": 1}' \
  http://localhost:8000/api/notifications/read/

# Mark all notifications as read
curl -X PATCH \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mark_all": true}' \
  http://localhost:8000/api/notifications/read/
```

---

## Notification Types

The system supports three notification types:

1. **order_update**: Order-related notifications (status changes, rider assignment)
2. **payment**: Payment-related notifications (completion, failures)
3. **system**: General system notifications

---

## Integration Guide

### Sending Notifications from Django Code

#### Method 1: Using Utility Functions (Recommended)

```python
from notifications.utils import (
    send_order_update_notification,
    send_rider_assignment_notification,
    send_payment_notification,
    send_system_notification
)

# Order update
send_order_update_notification(
    user_id=user.id,
    order_id=123,
    status="confirmed",
    additional_info="Estimated delivery: Tomorrow"
)

# Rider assignment
send_rider_assignment_notification(
    user_id=user.id,
    order_id=123,
    rider_name="John Doe"
)

# Payment
send_payment_notification(
    user_id=user.id,
    payment_id=456,
    amount=1000,
    status="completed"
)

# System notification
send_system_notification(
    user_id=user.id,
    title="Welcome!",
    message="Welcome to our platform"
)
```

#### Method 2: Direct Task Call

```python
from notifications.tasks import send_notification_task

# Basic usage
send_notification_task.delay(
    user_id=1,
    title="Custom Title",
    message="Custom message",
    notification_type="system"
)

# With options
send_notification_task.apply_async(
    args=[user_id, title, message, notification_type],
    queue="notifications",
    countdown=60,  # Delay by 60 seconds
    retry=True
)
```

#### Method 3: Using Django Signals

```python
# In your app's signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from orders.models import Order
from notifications.utils import send_order_update_notification

@receiver(post_save, sender=Order)
def order_status_changed(sender, instance, created, **kwargs):
    if not created and instance.status:
        send_order_update_notification(
            user_id=instance.user_id,
            order_id=instance.id,
            status=instance.status
        )
```

---

## Database Schema

### Notification Model

```python
class Notification(models.Model):
    user = ForeignKey(User)              # User receiving the notification
    title = CharField(max_length=255)    # Notification title
    message = TextField()                # Notification message
    type = CharField(max_length=20)      # Type: order_update, payment, system
    is_read = BooleanField(default=False) # Read status
    created_at = DateTimeField()         # Creation timestamp
    
    # Indexes:
    # - (user, created_at)
    # - (user, is_read)
```

---

## Performance Considerations

1. **Indexes**: Composite indexes on `(user, created_at)` and `(user, is_read)` ensure fast queries
2. **Pagination**: Default page size of 20, max 100 to prevent large result sets
3. **Async Processing**: Celery handles notification creation asynchronously
4. **Retry Mechanism**: Tasks retry with exponential backoff (max 3 retries)
5. **Cleanup**: Periodic task removes read notifications older than 90 days

---

## Error Handling

### Task Failures
- Automatic retry with exponential backoff
- Max 3 retries with jitter to prevent thundering herd
- Failed tasks logged with full error details

### API Errors
- `400`: Invalid request (missing parameters, validation errors)
- `401`: Authentication required
- `404`: Resource not found
- `500`: Server error (logged and monitored)

---

## Monitoring

### Celery Task Status
```python
from notifications.tasks import send_notification_task

# Send task
result = send_notification_task.delay(user_id, title, message, type)

# Check status
print(result.id)        # Task ID
print(result.ready())   # Is complete?
print(result.result)    # Task result
```

### RabbitMQ Queue Monitoring
- Access RabbitMQ Management UI: `http://localhost:15672`
- Default credentials: `guest/guest`
- Monitor queue depth, throughput, and consumer status

### Celery Flower (Web UI)
```bash
pip install flower
celery -A backend flower
# Access at http://localhost:5555
```

---

## Security

1. **Authentication**: All endpoints require valid authentication token
2. **Authorization**: Users can only access their own notifications
3. **Input Validation**: All inputs validated and sanitized
4. **Rate Limiting**: API endpoints protected by DRF throttling
5. **SQL Injection**: Protected by Django ORM parameterized queries

---

## Examples

### Complete Order Flow with Notifications

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from orders.models import Order
from notifications.utils import send_order_update_notification

class OrderCreateView(APIView):
    def post(self, request):
        # Create order
        order = Order.objects.create(
            user=request.user,
            # ... other fields
        )
        
        # Send notification
        send_order_update_notification(
            user_id=request.user.id,
            order_id=order.id,
            status="created",
            additional_info="Your order has been successfully placed"
        )
        
        return Response({"order_id": order.id})
```

### Bulk Notifications

```python
from accounts.models import User
from notifications.utils import send_system_notification

def send_maintenance_alert():
    """Send maintenance alert to all active users"""
    active_users = User.objects.filter(is_active=True)
    
    for user in active_users:
        send_system_notification(
            user_id=user.id,
            title="Scheduled Maintenance",
            message="System will be down for maintenance on Jan 15, 2025"
        )
```

