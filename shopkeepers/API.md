# Shopkeeper API Documentation

This document describes all the API endpoints available for the Shopkeeper (Customer) module.

**Base URL:** `/api/shopkeepers/`

**Authentication:** All endpoints require authentication. Include the JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

**Permissions:** All endpoints require the user to have the `SHOPKEEPER` role.

---

## Table of Contents
1. [Order Management](#order-management)
2. [Order Tracking](#order-tracking)
3. [Payment Records](#payment-records)
4. [Inventory Browsing](#inventory-browsing)
5. [Notifications](#notifications)
6. [Support & Feedback](#support--feedback)
7. [Analytics](#analytics)

---

## Order Management

### 1. Create Order
**POST** `/api/shopkeepers/orders/create/`

Create a new order from a warehouse.

**Request Body:**
```json
{
  "warehouse": 1,
  "items": [
    {
      "item_id": 5,
      "quantity": 10
    },
    {
      "item_id": 8,
      "quantity": 5
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "id": 42,
  "warehouse": 1,
  "warehouse_name": "Main Warehouse",
  "warehouse_address": "123 Main St, City",
  "status": "pending",
  "total_amount": "1250.00",
  "order_items": [
    {
      "id": 1,
      "item": 5,
      "item_name": "Rice Bag 5kg",
      "item_sku": "RICE-5KG",
      "quantity": 10,
      "price": "100.00"
    }
  ],
  "delivery_status": null,
  "rider_info": null,
  "created_at": "2025-10-23T10:30:00Z",
  "updated_at": "2025-10-23T10:30:00Z"
}
```

---

### 2. List Orders
**GET** `/api/shopkeepers/orders/`

Get a paginated list of all orders.

**Query Parameters:**
- `status` (optional): Filter by status (pending, accepted, rejected, in_transit, delivered, cancelled)
- `start_date` (optional): Filter orders from this date (YYYY-MM-DD)
- `end_date` (optional): Filter orders until this date (YYYY-MM-DD)
- `ordering` (optional): Sort by field (e.g., `-created_at`, `total_amount`)
- `page` (optional): Page number
- `page_size` (optional): Items per page (default: 20, max: 100)

**Example:** `/api/shopkeepers/orders/?status=pending&ordering=-created_at&page=1`

**Response (200 OK):**
```json
{
  "count": 25,
  "next": "http://example.com/api/shopkeepers/orders/?page=2",
  "previous": null,
  "results": [
    {
      "id": 42,
      "warehouse": 1,
      "warehouse_name": "Main Warehouse",
      "warehouse_address": "123 Main St, City",
      "status": "pending",
      "total_amount": "1250.00",
      "order_items": [...],
      "delivery_status": null,
      "rider_info": null,
      "created_at": "2025-10-23T10:30:00Z",
      "updated_at": "2025-10-23T10:30:00Z"
    }
  ]
}
```

---

### 3. Get Order Details
**GET** `/api/shopkeepers/orders/{id}/`

Get detailed information about a specific order.

**Response (200 OK):**
```json
{
  "id": 42,
  "warehouse": 1,
  "warehouse_name": "Main Warehouse",
  "warehouse_address": "123 Main St, City",
  "status": "in_transit",
  "total_amount": "1250.00",
  "order_items": [
    {
      "id": 1,
      "item": 5,
      "item_name": "Rice Bag 5kg",
      "item_sku": "RICE-5KG",
      "quantity": 10,
      "price": "100.00"
    }
  ],
  "delivery_status": "in_transit",
  "rider_info": {
    "rider_id": 15,
    "rider_phone": "+919876543210",
    "delivery_fee": "50.00"
  },
  "created_at": "2025-10-23T10:30:00Z",
  "updated_at": "2025-10-23T11:15:00Z"
}
```

---

### 4. Update Order (Cancel)
**PATCH** `/api/shopkeepers/orders/{id}/update/`

Cancel an order (only possible if status is pending or accepted).

**Request Body:**
```json
{
  "status": "cancelled"
}
```

**Response (200 OK):**
```json
{
  "id": 42,
  "warehouse": 1,
  "status": "cancelled",
  ...
}
```

---

## Order Tracking

### 5. Track Order
**GET** `/api/shopkeepers/orders/{id}/tracking/`

Get real-time tracking information for an order including delivery status and rider details.

**Response (200 OK):**
```json
{
  "order_id": 42,
  "order_status": "in_transit",
  "order_status_display": "In Transit",
  "total_amount": "1250.00",
  "created_at": "2025-10-23T10:30:00Z",
  "updated_at": "2025-10-23T11:15:00Z",
  "warehouse": {
    "id": 1,
    "name": "Main Warehouse",
    "address": "123 Main St, City"
  },
  "delivery": {
    "status": "in_transit",
    "status_display": "In Transit",
    "delivery_fee": "50.00",
    "created_at": "2025-10-23T11:00:00Z",
    "updated_at": "2025-10-23T11:15:00Z"
  },
  "rider": {
    "id": 15,
    "phone_number": "+919876543210"
  }
}
```

---

## Payment Records

### 6. List Payment Transactions
**GET** `/api/shopkeepers/payments/`

Get a paginated list of all payment transactions.

**Query Parameters:**
- `status` (optional): Filter by status (pending, completed, failed)
- `start_date` (optional): Filter from this date
- `end_date` (optional): Filter until this date
- `ordering` (optional): Sort by field (e.g., `-created_at`, `amount`)
- `page`, `page_size`: Pagination parameters

**Response (200 OK):**
```json
{
  "count": 15,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 25,
      "order_id": 42,
      "warehouse_name": "Main Warehouse",
      "payment_type": "shopkeeper_to_warehouse",
      "payment_type_display": "Shopkeeper to Warehouse",
      "status": "completed",
      "status_display": "Completed",
      "amount": "1250.00",
      "payment_method": "upi",
      "transaction_id": "TXN123456789",
      "notes": "",
      "created_at": "2025-10-23T10:30:00Z",
      "completed_at": "2025-10-23T10:31:00Z"
    }
  ]
}
```

---

### 7. Payment Summary
**GET** `/api/shopkeepers/payments/summary/`

Get a summary of all payments including pending dues.

**Response (200 OK):**
```json
{
  "total_paid": "15000.00",
  "total_pending": "2500.00",
  "total_failed": "0.00",
  "pending_orders_count": 3,
  "completed_payments_count": 25
}
```

---

## Inventory Browsing

### 8. Browse Inventory
**GET** `/api/shopkeepers/inventory/browse/`

Browse products from warehouses with filters and search.

**Query Parameters:**
- `warehouse` (optional): Filter by warehouse ID
- `search` (optional): Search in name, description, or SKU
- `min_price` (optional): Minimum price filter
- `max_price` (optional): Maximum price filter
- `in_stock` (optional): Filter only in-stock items (true/false)
- `ordering` (optional): Sort by field (e.g., `name`, `price`, `-created_at`)
- `page`, `page_size`: Pagination parameters

**Example:** `/api/shopkeepers/inventory/browse/?warehouse=1&search=rice&in_stock=true&ordering=price`

**Response (200 OK):**
```json
{
  "count": 50,
  "next": "...",
  "previous": null,
  "results": [
    {
      "id": 5,
      "warehouse_id": 1,
      "warehouse_name": "Main Warehouse",
      "warehouse_address": "123 Main St, City",
      "name": "Rice Bag 5kg",
      "description": "Premium basmati rice",
      "sku": "RICE-5KG",
      "price": "100.00",
      "quantity": 150,
      "in_stock": true,
      "created_at": "2025-10-20T09:00:00Z",
      "updated_at": "2025-10-23T08:00:00Z"
    }
  ]
}
```

---

### 9. Nearby Warehouses (Optimized)
**GET** `/api/shopkeepers/warehouses/nearby/`

Get the nearest warehouse based on GPS location with optimized PostGIS spatial queries and Redis caching.

**Query Parameters:**
- `latitude` (required): User's GPS latitude coordinate (-90 to 90)
- `longitude` (required): User's GPS longitude coordinate (-180 to 180)
- `radius` (optional): Search radius in kilometers (default: 10, range: 1-50)

**Example:** `/api/shopkeepers/warehouses/nearby/?latitude=28.6139&longitude=77.2090&radius=15`

**Response (200 OK - Warehouse Found):**
```json
{
  "nearest_warehouse": {
    "id": 1,
    "name": "Main Warehouse",
    "address": "123 Main St, City",
    "distance_km": 2.5
  },
  "total_nearby": 3
}
```

**Response (200 OK - No Warehouse Found):**
```json
{
  "nearest_warehouse": null,
  "total_nearby": 0,
  "message": "No warehouses found within 15 km radius."
}
```

**Performance Features:**
- Uses PostGIS spatial index for fast distance calculations
- Returns only the single closest warehouse within radius
- Query results cached in Redis for 5 minutes per (lat, lon, radius) combination
- Only returns active and approved warehouses

**Error Response (400 Bad Request - Missing Coordinates):**
```json
{
  "error": "Missing coordinates. Both 'latitude' and 'longitude' query parameters are required."
}
```

**Error Response (400 Bad Request - Invalid Coordinates):**
```json
{
  "error": "Invalid coordinates. 'latitude' and 'longitude' must be valid numbers."
}
```

**Error Response (400 Bad Request - Invalid Latitude):**
```json
{
  "error": "Invalid latitude. Latitude must be between -90 and 90 degrees."
}
```

**Error Response (400 Bad Request - Invalid Longitude):**
```json
{
  "error": "Invalid longitude. Longitude must be between -180 and 180 degrees."
}
```

**Error Response (400 Bad Request - Invalid Radius):**
```json
{
  "error": "Invalid radius. Radius must be between 1 and 50 kilometers."
}
```

---

## Notifications

### 10. List Notifications
**GET** `/api/shopkeepers/notifications/`

Get all notifications for the authenticated shopkeeper.

**Query Parameters:**
- `is_read` (optional): Filter by read status (true/false)
- `page`, `page_size`: Pagination parameters

**Response (200 OK):**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 15,
      "notification_type": "order_accepted",
      "notification_type_display": "Order Accepted",
      "title": "Order Accepted",
      "message": "Your order #42 has been accepted by the warehouse.",
      "order_id": 42,
      "is_read": false,
      "created_at": "2025-10-23T10:35:00Z"
    }
  ]
}
```

---

### 11. Mark Notifications as Read
**POST** `/api/shopkeepers/notifications/mark-read/`

Mark one or more notifications as read.

**Request Body (mark specific notifications):**
```json
{
  "notification_ids": [15, 16, 17]
}
```

**Request Body (mark all as read):**
```json
{}
```

**Response (200 OK):**
```json
{
  "message": "3 notification(s) marked as read."
}
```

---

### 12. Unread Notification Count
**GET** `/api/shopkeepers/notifications/unread-count/`

Get the count of unread notifications.

**Response (200 OK):**
```json
{
  "unread_count": 5
}
```

---

## Support & Feedback

### 13. List Support Tickets
**GET** `/api/shopkeepers/support/tickets/`

Get all support tickets created by the shopkeeper.

**Query Parameters:**
- `status` (optional): Filter by status (open, in_progress, resolved, closed)
- `category` (optional): Filter by category (order_issue, payment_issue, delivery_issue, app_bug, feature_request, feedback, other)
- `page`, `page_size`: Pagination parameters

**Response (200 OK):**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 8,
      "category": "order_issue",
      "category_display": "Order Issue",
      "subject": "Wrong item delivered",
      "description": "I ordered rice but received wheat instead.",
      "order_id": 40,
      "status": "open",
      "status_display": "Open",
      "priority": "high",
      "priority_display": "High",
      "created_at": "2025-10-23T09:00:00Z",
      "updated_at": "2025-10-23T09:00:00Z",
      "resolved_at": null
    }
  ]
}
```

---

### 14. Create Support Ticket
**POST** `/api/shopkeepers/support/tickets/create/`

Create a new support ticket or submit feedback.

**Request Body:**
```json
{
  "category": "order_issue",
  "subject": "Wrong item delivered",
  "description": "I ordered rice but received wheat instead. Order #40.",
  "order": 40
}
```

**Note:** The `order` field is optional.

**Response (201 Created):**
```json
{
  "id": 8,
  "category": "order_issue",
  "category_display": "Order Issue",
  "subject": "Wrong item delivered",
  "description": "I ordered rice but received wheat instead. Order #40.",
  "order_id": 40,
  "status": "open",
  "status_display": "Open",
  "priority": "medium",
  "priority_display": "Medium",
  "created_at": "2025-10-23T09:00:00Z",
  "updated_at": "2025-10-23T09:00:00Z",
  "resolved_at": null
}
```

---

### 15. Get Support Ticket Details
**GET** `/api/shopkeepers/support/tickets/{id}/`

Get details of a specific support ticket.

**Response (200 OK):**
```json
{
  "id": 8,
  "category": "order_issue",
  "category_display": "Order Issue",
  "subject": "Wrong item delivered",
  "description": "I ordered rice but received wheat instead. Order #40.",
  "order_id": 40,
  "status": "resolved",
  "status_display": "Resolved",
  "priority": "high",
  "priority_display": "High",
  "created_at": "2025-10-23T09:00:00Z",
  "updated_at": "2025-10-23T14:00:00Z",
  "resolved_at": "2025-10-23T14:00:00Z"
}
```

---

## Analytics

### 16. Analytics Summary
**GET** `/api/shopkeepers/analytics/`

Get comprehensive analytics including monthly breakdown of orders and spending.

**Query Parameters:**
- `months` (optional): Number of months to include (default: 6)

**Example:** `/api/shopkeepers/analytics/?months=12`

**Response (200 OK):**
```json
{
  "total_orders": 150,
  "total_spending": "125000.00",
  "pending_orders": 5,
  "completed_orders": 130,
  "cancelled_orders": 15,
  "average_order_value": "833.33",
  "monthly_data": [
    {
      "month": "October",
      "year": 2025,
      "total_orders": 25,
      "completed_orders": 20,
      "cancelled_orders": 3,
      "total_spending": "20000.00",
      "average_order_value": "800.00"
    },
    {
      "month": "September",
      "year": 2025,
      "total_orders": 30,
      "completed_orders": 28,
      "cancelled_orders": 2,
      "total_spending": "25000.00",
      "average_order_value": "833.33"
    }
  ]
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Invalid input data",
  "details": {
    "warehouse": ["This field is required."]
  }
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "error": "Order not found."
}
```

### 500 Internal Server Error
```json
{
  "error": "An unexpected error occurred."
}
```

---

## Technical Implementation Details

### Recent Updates (October 2025)

The following technical improvements have been implemented:

#### 1. **User Model Structure**
- The custom User model uses `phone_number` as the `USERNAME_FIELD`
- No `username` field exists; authentication is phone-based
- User identification in all responses uses `phone_number`

#### 2. **Order-Warehouse Relationship**
- The `Order.warehouse` field is a ForeignKey to the `Warehouse` model (not User)
- This provides direct access to warehouse attributes:
  - `order.warehouse.name` - Warehouse name
  - `order.warehouse.address` - Warehouse address
  - `order.warehouse.location` - PostGIS Point field for geospatial queries

#### 3. **PostGIS Distance Calculations**
- Warehouse proximity features use PostGIS for accurate distance calculations
- Two Distance classes are used:
  - `django.contrib.gis.db.models.functions.Distance` - For database annotations
  - `django.contrib.gis.measure.Distance` - For distance measurements (e.g., `Distance(km=10)`)
- Distance calculations return values in kilometers with 2 decimal precision

#### 4. **Query Parameters**
- All list views support Django Rest Framework's `query_params` for filtering
- Common filters include: `status`, `start_date`, `end_date`, `ordering`, `page`, `page_size`
- The API uses DRF's Request wrapper (not Django's HttpRequest) which provides `query_params`

### Database Schema Notes

- **Users Table**: Custom user model with phone-based auth (no username field)
- **Orders Table**: `warehouse` field is ForeignKey to `warehouses_warehouse` table
- **Location Fields**: PostGIS PointField for geographic data (SRID 4326)
- **Distance Annotations**: Use PostGIS's Distance function for km-based calculations

---

## Notes

1. **Authentication**: All datetime fields are in ISO 8601 format (UTC timezone)
2. **Data Types**: All amount fields are strings representing decimal values
3. **Pagination**: Uses the standard DRF format with `count`, `next`, `previous`, and `results`
4. **Authorization**: All endpoints require authentication with a valid JWT token
5. **Location Services**: The shopkeeper must have completed their profile (including location) to use warehouse proximity features
6. **User Identification**: The custom User model uses `phone_number` as the primary identifier (not username)
7. **Warehouse References**: All order warehouse fields reference the Warehouse model (not User), providing access to warehouse name, address, and location data
8. **PostGIS Integration**: Distance calculations for nearby warehouses use PostGIS geographic functions for accurate kilometer-based measurements

