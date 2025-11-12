# Analytics API Documentation

## Overview
The Analytics API provides endpoints for accessing pre-computed analytics summaries for different entity types (system-wide, warehouse, rider, and shopkeeper). Analytics data is computed daily via Celery tasks and cached for performance.

## Base URL
```
/api/analytics/
```

## Authentication
All endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

## Permissions
- **System Analytics**: Admin only
- **Warehouse Analytics**: Admin and Warehouse Managers (managers can only see their own warehouse)
- **Rider Analytics**: Admin and Riders (riders can only see their own analytics)
- **Shopkeeper Analytics**: Admin and Shopkeepers (shopkeepers can only see their own analytics)

## Endpoints

### 1. List Analytics Summaries
```
GET /api/analytics/
```

**Description**: List all analytics summaries accessible to the authenticated user. Results are filtered based on user role.

**Query Parameters**:
- `ref_type` (optional): Filter by entity type (`system`, `warehouse`, `rider`, `shopkeeper`)
- `ref_id` (optional): Filter by entity ID
- `date` (optional): Filter by date (YYYY-MM-DD)

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "ref_type": "system",
    "ref_id": null,
    "date": "2025-11-09",
    "metrics": {
      "total_orders": 150,
      "total_revenue": 45000.50,
      "active_users": 75,
      "average_delivery_time": 28.5,
      "daily_growth": 5.2,
      "pending_orders": 12,
      "completed_orders": 138,
      "active_riders": 25,
      "active_warehouses": 8
    },
    "created_at": "2025-11-10T00:15:00Z"
  }
]
```

---

### 2. Get System Analytics
```
GET /api/analytics/system/
```

**Description**: Get system-wide analytics for specified date range.

**Permissions**: Admin only

**Query Parameters**:
- `date` (optional): Target date (YYYY-MM-DD). Default: yesterday
- `days` (optional): Number of days to fetch. Default: 7

**Response** (200 OK):
```json
[
  {
    "date": "2025-11-09",
    "total_orders": 150,
    "total_revenue": 45000.50,
    "active_users": 75,
    "average_delivery_time": 28.5,
    "daily_growth": 5.2,
    "pending_orders": 12,
    "completed_orders": 138,
    "active_riders": 25,
    "active_warehouses": 8
  },
  {
    "date": "2025-11-08",
    "total_orders": 142,
    "total_revenue": 42800.00,
    ...
  }
]
```

**Response** (202 Accepted):
```json
{
  "message": "Analytics are being computed. Please try again in a moment."
}
```

---

### 3. Get Warehouse Analytics
```
GET /api/analytics/warehouse/
```

**Description**: Get warehouse-specific analytics for specified date range.

**Permissions**: Admin and Warehouse Managers (managers auto-scoped to their warehouse)

**Query Parameters**:
- `warehouse_id` (required for admin, auto-filled for managers): Warehouse ID
- `date` (optional): Target date (YYYY-MM-DD). Default: yesterday
- `days` (optional): Number of days to fetch. Default: 7

**Response** (200 OK):
```json
[
  {
    "date": "2025-11-09",
    "warehouse_id": 5,
    "warehouse_name": "Downtown Warehouse",
    "total_orders": 45,
    "total_revenue": 13500.00,
    "completion_rate": 92.0,
    "average_delivery_time": 25.3,
    "pending_orders": 3,
    "completed_orders": 41,
    "rejected_orders": 1,
    "active_riders": 8
  }
]
```

**Errors**:
- `400 Bad Request`: Missing warehouse_id (for admin users)

---

### 4. Get Rider Analytics
```
GET /api/analytics/rider/
```

**Description**: Get rider-specific analytics for specified date range.

**Permissions**: Admin and Riders (riders auto-scoped to their own data)

**Query Parameters**:
- `rider_id` (required for admin, auto-filled for riders): Rider ID
- `date` (optional): Target date (YYYY-MM-DD). Default: yesterday
- `days` (optional): Number of days to fetch. Default: 7

**Response** (200 OK):
```json
[
  {
    "date": "2025-11-09",
    "rider_id": 12,
    "rider_name": "John Doe",
    "completed_deliveries": 18,
    "total_distance": 45.2,
    "total_earnings": 540.00,
    "average_delivery_time": 22.5,
    "on_time_deliveries": 16,
    "late_deliveries": 2,
    "on_time_ratio": 88.89
  }
]
```

**Errors**:
- `400 Bad Request`: Missing rider_id (for admin) or rider profile not found

---

### 5. Refresh Analytics
```
POST /api/analytics/refresh/
```

**Description**: Manually trigger analytics computation for a specific entity and date.

**Permissions**: Admin only

**Request Body**:
```json
{
  "type": "system",
  "id": null,
  "date": "2025-11-09"
}
```

**Fields**:
- `type` (required): Analytics type (`system`, `warehouse`, or `rider`)
- `id` (required for warehouse/rider): Entity ID
- `date` (optional): Date to compute (YYYY-MM-DD). Default: yesterday

**Response** (202 Accepted):
```json
{
  "message": "System analytics computation triggered"
}
```

**Errors**:
- `400 Bad Request`: Invalid type or missing required ID

---

## Metrics Details

### System Metrics
- `total_orders`: Total number of orders
- `total_revenue`: Total revenue in currency
- `active_users`: Number of unique shopkeepers who placed orders
- `average_delivery_time`: Average delivery time in minutes
- `daily_growth`: Percentage growth compared to previous day
- `pending_orders`: Orders pending or accepted
- `completed_orders`: Delivered orders
- `active_riders`: Number of riders who made deliveries
- `active_warehouses`: Number of warehouses that received orders

### Warehouse Metrics
- `warehouse_name`: Name of the warehouse
- `total_orders`: Orders for this warehouse
- `total_revenue`: Revenue from this warehouse
- `completion_rate`: Percentage of orders completed
- `average_delivery_time`: Average delivery time in minutes
- `pending_orders`: Pending/accepted orders
- `completed_orders`: Delivered orders
- `rejected_orders`: Rejected orders
- `active_riders`: Available riders at this warehouse

### Rider Metrics
- `rider_name`: Full name of the rider
- `completed_deliveries`: Number of completed deliveries
- `total_distance`: Total distance traveled (km)
- `total_earnings`: Total earnings from deliveries
- `average_delivery_time`: Average delivery time in minutes
- `on_time_deliveries`: Deliveries completed within 30 minutes
- `late_deliveries`: Deliveries that took > 30 minutes
- `on_time_ratio`: Percentage of on-time deliveries

### Shopkeeper Metrics
- `orders_placed`: Number of orders placed
- `total_spent`: Total amount spent
- `most_frequent_warehouse`: Most frequently used warehouse
- `repeat_rate`: Percentage of orders from most frequent warehouse
- `pending_orders`: Pending/accepted orders
- `completed_orders`: Delivered orders
- `cancelled_orders`: Cancelled orders

---

## Celery Tasks

### compute_daily_summaries
**Schedule**: Runs nightly at 00:15 UTC

Computes analytics for all entity types (system, warehouse, rider, shopkeeper) for the previous day.

### compute_system_analytics
**On-demand**: Triggered via refresh endpoint or scheduled

Computes system-wide analytics for a specific date.

### compute_warehouse_analytics
**On-demand**: Triggered via refresh endpoint

Computes warehouse-specific analytics for a specific date.

### compute_rider_analytics
**On-demand**: Triggered via refresh endpoint

Computes rider-specific analytics for a specific date.

---

## Caching
Analytics data is cached for 1 hour to improve performance. Cache keys follow the pattern:
- System: `system_analytics_{date}_{days}`
- Warehouse: `warehouse_analytics_{warehouse_id}_{date}_{days}`
- Rider: `rider_analytics_{rider_id}_{date}_{days}`

---

## Error Responses

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
  "detail": "Not found."
}
```

### 400 Bad Request
```json
{
  "error": "warehouse_id is required"
}
```

---

## Examples

### Get Last 7 Days of System Analytics
```bash
curl -X GET "https://api.example.com/api/analytics/system/?days=7" \
  -H "Authorization: Bearer <token>"
```

### Get Warehouse Analytics for Specific Date
```bash
curl -X GET "https://api.example.com/api/analytics/warehouse/?warehouse_id=5&date=2025-11-09&days=1" \
  -H "Authorization: Bearer <token>"
```

### Trigger Analytics Refresh
```bash
curl -X POST "https://api.example.com/api/analytics/refresh/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "warehouse",
    "id": 5,
    "date": "2025-11-09"
  }'
```

