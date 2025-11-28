# GEMINI API Documentation

## Overview
This API powers the GEMINI platform, facilitating interactions between Shopkeepers, Warehouses, and Riders.

**Base URL:** `/api/`
**Authentication:** Token-based (Header: `Authorization: Token <your_token>`)
**Content-Type:** `application/json`

---

## 1. Authentication & Accounts
**Base URL:** `/api/accounts/`

### Send OTP
Generates and sends an OTP to the provided mobile number.
- **URL:** `/send-otp/`
- **Method:** `POST`
- **Body:**
  ```json
  {
    "phone_number": "+1234567890"
  }
  ```
- **Response:** `200 OK`
  ```json
  {
    "message": "OTP sent successfully"
  }
  ```

### Verify OTP
Verifies the OTP and returns an authentication token.
- **URL:** `/verify-otp/`
- **Method:** `POST`
- **Body:**
  ```json
  {
    "phone_number": "+1234567890",
    "otp": "123456"
  }
  ```
- **Response:** `200 OK`
  ```json
  {
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
    "user_id": 1,
    "role": "SHOPKEEPER"
  }
  ```

### Current User
Get details of the currently authenticated user.
- **URL:** `/me/`
- **Method:** `GET`
- **Headers:** `Authorization: Token <token>`
- **Response:** `200 OK`
  ```json
  {
    "id": 1,
    "phone_number": "+1234567890",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "SHOPKEEPER"
  }
  ```

### Logout
Invalidates the current token.
- **URL:** `/logout/`
- **Method:** `POST`
- **Headers:** `Authorization: Token <token>`
- **Response:** `200 OK`

---

## 2. Shopkeeper API
**Base URL:** `/api/shopkeepers/`
**Role Required:** `SHOPKEEPER`

### Create Order
Create a new order from a specific warehouse.
- **URL:** `/orders/create/`
- **Method:** `POST`
- **Body:**
  ```json
  {
    "warehouse": 1,
    "items": [
      {
        "item_id": 101,
        "quantity": 5
      },
      {
        "item_id": 102,
        "quantity": 2
      }
    ]
  }
  ```
- **Response:** `201 Created`
  ```json
  {
    "id": 501,
    "status": "pending",
    "total_amount": "150.00",
    "created_at": "2023-10-27T10:00:00Z"
  }
  ```

### List Orders
Get a list of all orders placed by the shopkeeper.
- **URL:** `/orders/`
- **Method:** `GET`
- **Response:** `200 OK`
  ```json
  [
    {
      "id": 501,
      "warehouse_name": "Central Warehouse",
      "status": "pending",
      "total_amount": "150.00",
      "created_at": "2023-10-27T10:00:00Z"
    }
  ]
  ```

### Order Detail
Get detailed information about a specific order.
- **URL:** `/orders/<id>/`
- **Method:** `GET`
- **Response:** `200 OK`

### Order Tracking
Get tracking information for an active order.
- **URL:** `/orders/<id>/tracking/`
- **Method:** `GET`
- **Response:** `200 OK`
  ```json
  {
    "status": "in_transit",
    "rider_location": {
      "lat": 12.9716,
      "lng": 77.5946
    },
    "estimated_arrival": "10 mins"
  }
  ```

### Browse Inventory
Browse items available in warehouses.
- **URL:** `/inventory/browse/`
- **Method:** `GET`
- **Query Params:** `warehouse_id` (optional), `search` (optional)
- **Response:** `200 OK`
  ```json
  [
    {
      "id": 101,
      "name": "Rice 25kg",
      "price": "1200.00",
      "in_stock": true
    }
  ]
  ```

### Nearby Warehouses
Find warehouses near the shopkeeper's location.
- **URL:** `/warehouses/nearby/`
- **Method:** `GET`
- **Query Params:** `lat`, `lng`, `radius` (km)
- **Response:** `200 OK`
  ```json
  [
    {
      "id": 1,
      "name": "Central Warehouse",
      "distance_km": 2.5
    }
  ]
  ```

### Shopkeeper Analytics
Get spending and order analytics.
- **URL:** `/analytics/`
- **Method:** `GET`
- **Response:** `200 OK`

---

## 3. Warehouse API
**Base URL:** `/api/warehouses/`
**Role Required:** `WAREHOUSE_MANAGER` (or `SUPER_ADMIN`)

### List Warehouses
- **URL:** `/`
- **Method:** `GET`

### Warehouse Detail
- **URL:** `/<id>/`
- **Method:** `GET`

### Assign Rider
Manually assign a rider to an order.
- **URL:** `/<id>/assign_rider/`
- **Method:** `POST`
- **Body:**
  ```json
  {
    "order_id": 501,
    "rider_id": 20
  }
  ```
- **Response:** `200 OK`

### Warehouse Deliveries
Track deliveries managed by this warehouse.
- **URL:** `/<id>/deliveries/`
- **Method:** `GET`
- **Query Params:** `status` (active/completed/all)

### Warehouse Notifications
- **URL:** `/<id>/notifications/`
- **Method:** `GET`
- **Query Params:** `is_read` (true/false), `type`

### Mark Notifications Read
- **URL:** `/<id>/notifications/mark-read/`
- **Method:** `POST`
- **Body:**
  ```json
  {
    "notification_ids": [1, 2, 3]
  }
  ```

### Rider Payouts
View payouts for riders associated with this warehouse.
- **URL:** `/<id>/rider-payouts/`
- **Method:** `GET`
- **Query Params:** `status`

### Analytics Summary
Get a summary of warehouse performance.
- **URL:** `/<id>/analytics/summary/`
- **Method:** `GET`
- **Query Params:** `from_date`, `to_date`
- **Response:** `200 OK`
  ```json
  {
    "total_orders": 150,
    "completed_orders": 145,
    "total_revenue": "50000.00",
    "top_items": [...]
  }
  ```

### Export Analytics
Download analytics data.
- **URL:** `/<id>/analytics/export/`
- **Method:** `GET`
- **Query Params:** `format` (json/csv), `from_date`, `to_date`

---

## 4. Rider API
**Base URL:** `/api/riders/`
**Role Required:** `RIDER`

### Register Rider
(Admin/Warehouse Admin only)
- **URL:** `/rider/register/`
- **Method:** `POST`
- **Body:**
  ```json
  {
    "user_id": 5,
    "warehouse_id": 1,
    "status": "active"
  }
  ```

### Rider Profile
- **URL:** `/rider/profile/`
- **Method:** `GET`

### Update Location
Update the rider's live location.
- **URL:** `/rider/location/update/`
- **Method:** `POST`
- **Body:**
  ```json
  {
    "latitude": 12.9716,
    "longitude": 77.5946
  }
  ```

### Update Availability
- **URL:** `/rider/availability/update/`
- **Method:** `POST`
- **Body:**
  ```json
  {
    "availability": "available"  // or "off-duty"
  }
  ```

### Earnings
Get earnings summary.
- **URL:** `/rider/earnings/`
- **Method:** `GET`

### Delivery History
- **URL:** `/rider/history/`
- **Method:** `GET`

---

## 5. Orders API (Shared/Specific)
**Base URL:** `/api/orders/` or `/api/shopkeeper/orders/` / `/api/warehouse/orders/`

### Shopkeeper: Create Order
- **URL:** `/shopkeeper/orders/create/`
- **Method:** `POST`
- **Body:** (Same as Shopkeeper API)

### Warehouse: List Orders
- **URL:** `/warehouse/orders/`
- **Method:** `GET`

### Warehouse: Accept Order
- **URL:** `/warehouse/orders/<id>/accept/`
- **Method:** `POST`

### Warehouse: Reject Order
- **URL:** `/warehouse/orders/<id>/reject/`
- **Method:** `POST`
- **Body:**
  ```json
  {
    "reason": "Out of stock"
  }
  ```

---

## 6. Payments API
**Base URL:** `/api/payments/`

### Initiate Payment
- **URL:** `/initiate/`
- **Method:** `POST`

### Confirm Payment
- **URL:** `/confirm/`
- **Method:** `POST`

### Process Payouts (Admin/System)
- **URL:** `/payouts/process/`
- **Method:** `POST`
- **Body:**
  ```json
  {
    "order_ids": [501, 502]
  }
  ```

### List Payouts
- **URL:** `/payouts/list/`
- **Method:** `GET`
- **Query Params:** `status`

---

## 7. Notifications API
**Base URL:** `/api/notifications/`

### List Notifications
- **URL:** `/`
- **Method:** `GET`

### Mark as Read
- **URL:** `/read/`
- **Method:** `PATCH`
- **Body:**
  ```json
  {
    "notification_id": 1
  }
  ```
  OR
  ```json
  {
    "mark_all": true
  }
  ```

---

## 8. Analytics API (System)
**Base URL:** `/api/analytics/`
**Role Required:** `SUPER_ADMIN` (for system), `WAREHOUSE_MANAGER` (for warehouse), `RIDER` (for rider)

### System Analytics
- **URL:** `/system/`
- **Method:** `GET`
- **Query Params:** `date`, `days`

### Warehouse Analytics
- **URL:** `/warehouse/`
- **Method:** `GET`
- **Query Params:** `warehouse_id`, `date`, `days`

### Rider Analytics
- **URL:** `/rider/`
- **Method:** `GET`
- **Query Params:** `rider_id`, `date`, `days`

### Refresh Analytics (Admin)
- **URL:** `/refresh/`
- **Method:** `POST`
- **Body:**
  ```json
  {
    "type": "warehouse",
    "id": 1,
    "date": "2023-10-27"
  }
  ```
