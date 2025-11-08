
# API Documentation

This document provides a detailed overview of the API endpoints for the GEMINI platform, categorized by user roles: Admin, Warehouse, and Shopkeeper.

## Authentication

Authentication is handled via OTP and JWT tokens.

-   `POST /api/auth/send-otp/`: Sends an OTP to the user's registered email.
-   `POST /api/auth/verify-otp/`: Verifies the OTP and returns a JWT token for authenticated sessions.
-   `POST /api/auth/logout/`: Logs out the user and invalidates the session.
-   `GET /api/auth/me/`: Retrieves the profile of the currently authenticated user.

---

## Admin

Admin users (Super Admins) have full access to the system and can manage all aspects of the platform.

### Warehouse Management

-   **Endpoint:** `/api/warehouses/`
-   **Method:** `GET`
-   **Description:** Retrieves a list of all warehouses in the system.
-   **Permissions:** `IsSuperAdmin`
-   **Query Parameters:** `is_active`, `is_approved`, `search`, `ordering`
-   **Response:**
    ```json
    [
        {
            "id": 1,
            "name": "Main Warehouse",
            "address": "123 Main St, Anytown, USA",
            "is_active": true,
            "is_approved": true,
            "created_at": "2025-11-07T12:00:00Z"
        }
    ]
    ```

-   **Endpoint:** `/api/warehouses/{id}/`
-   **Method:** `GET`
-   **Description:** Retrieves the details of a specific warehouse.
-   **Permissions:** `IsSuperAdmin`
-   **Response:**
    ```json
    {
        "id": 1,
        "name": "Main Warehouse",
        "admin": 1,
        "address": "123 Main St, Anytown, USA",
        "is_active": true,
        "is_approved": true,
        "created_at": "2025-11-07T12:00:00Z",
        "updated_at": "2025-11-07T12:00:00Z"
    }
    ```

-   **Endpoint:** `/api/warehouses/`
-   **Method:** `POST`
-   **Description:** Creates a new warehouse. The user making the request will be set as the admin.
-   **Permissions:** `IsSuperAdmin`
-   **Request Body:**
    ```json
    {
        "name": "New Warehouse",
        "address": "456 Oak Ave, Otherville, USA"
    }
    ```

-   **Endpoint:** `/api/warehouses/{id}/`
-   **Method:** `PUT`, `PATCH`
-   **Description:** Updates the details of a specific warehouse.
-   **Permissions:** `IsSuperAdmin`
-   **Request Body:**
    ```json
    {
        "name": "Updated Warehouse Name",
        "is_active": false
    }
    ```

-   **Endpoint:** `/api/warehouses/{id}/`
-   **Method:** `DELETE`
-   **Description:** Deletes a specific warehouse.
-   **Permissions:** `IsSuperAdmin`

### Rider Management

-   **Endpoint:** `/api/admin/riders/manage/`
-   **Method:** `POST`
-   **Description:** Manages riders, including suspension, reactivation, and reassignment to a different warehouse.
-   **Permissions:** `IsSuperAdmin` or `IsWarehouseAdmin` (for their own riders)
-   **Request Body:**
    ```json
    {
        "action": "suspend",
        "rider_id": 2,
        "reason": "Repeated delivery delays."
    }
    ```
    or
    ```json
    {
        "action": "reassign",
        "rider_id": 2,
        "new_warehouse_id": 3
    }
    ```

-   **Endpoint:** `/api/admin/riders/export/payouts/`
-   **Method:** `GET`
-   **Description:** Exports rider payout and performance data as a CSV file.
-   **Permissions:** `IsSuperAdmin` or `IsWarehouseAdmin`
-   **Query Parameters:** `start_date`, `end_date`, `warehouse_id`

### Payment Management

-   **Endpoint:** `/api/payments/`
-   **Method:** `GET`
-   **Description:** Retrieves a list of all payments in the system.
-   **Permissions:** `IsSuperAdmin`
-   **Query Parameters:** `status`, `payment_type`, `warehouse`, `rider`, `order`, `ordering`, `search`
-   **Response:**
    ```json
    [
        {
            "id": 1,
            "transaction_id": "txn_12345",
            "order": 1,
            "warehouse": 1,
            "payer": 2,
            "payee": 3,
            "rider": null,
            "amount": "150.75",
            "status": "completed",
            "payment_type": "shopkeeper_to_warehouse",
            "created_at": "2025-11-07T10:00:00Z"
        }
    ]
    ```

-   **Endpoint:** `/api/payments/statistics/`
-   **Method:** `GET`
-   **Description:** Retrieves payment statistics.
-   **Permissions:** `IsSuperAdmin`
-   **Response:**
    ```json
    {
        "total_payments": 100,
        "pending": 10,
        "completed": 85,
        "failed": 5,
        "total_amount_pending": "1500.00",
        "total_amount_completed": "12500.00",
        "shopkeeper_payments": 60,
        "rider_payouts": 40
    }
    ```

---

## Warehouse

Warehouse managers can manage their own warehouses, inventory, orders, and riders.

### Warehouse Management

-   **Endpoint:** `/api/warehouses/`
-   **Method:** `GET`
-   **Description:** Retrieves a list of warehouses managed by the user.
-   **Permissions:** `IsWarehouseAdmin`
-   **Response:**
    ```json
    [
        {
            "id": 1,
            "name": "My Warehouse",
            "address": "123 Main St, Anytown, USA",
            "is_active": true,
            "is_approved": true
        }
    ]
    ```

### Inventory Management

-   **Endpoint:** `/api/warehouses/{id}/inventory/`
-   **Method:** `GET`
-   **Description:** Retrieves a list of all inventory items in a specific warehouse.
-   **Permissions:** `IsWarehouseAdmin`
-   **Query Parameters:** `search`
-   **Response:**
    ```json
    [
        {
            "id": 1,
            "name": "Item 1",
            "sku": "ITM001",
            "price": "10.00",
            "quantity": 100
        }
    ]
    ```

-   **Endpoint:** `/api/warehouses/{id}/inventory/bulk-update/`
-   **Method:** `POST`
-   **Description:** Bulk updates the stock levels of inventory items.
-   **Permissions:** `IsWarehouseAdmin`
-   **Request Body:**
    ```json
    {
        "updates": [
            {
                "item_id": 1,
                "quantity_change": -10
            },
            {
                "item_id": 2,
                "quantity_change": 20
            }
        ]
    }
    ```

### Order Management

-   **Endpoint:** `/api/warehouse/orders/`
-   **Method:** `GET`
-   **Description:** Retrieves a list of all orders for the warehouse, with optional status filtering.
-   **Permissions:** `IsWarehouseAdmin`
-   **Query Parameters:** `status`
-   **Response:**
    ```json
    [
        {
            "id": 1,
            "shopkeeper": 2,
            "warehouse": 1,
            "status": "pending",
            "total_amount": "150.75",
            "created_at": "2025-11-07T09:30:00Z"
        }
    ]
    ```

-   **Endpoint:** `/api/warehouse/orders/pending/`
-   **Method:** `GET`
-   **Description:** Retrieves a list of all pending orders for the warehouse.
-   **Permissions:** `IsWarehouseAdmin`

-   **Endpoint:** `/api/warehouse/orders/{id}/accept/`
-   **Method:** `POST`
-   **Description:** Accepts a pending order.
-   **Permissions:** `IsWarehouseAdmin`

-   **Endpoint:** `/api/warehouse/orders/{id}/reject/`
-   **Method:** `POST`
-   **Description:** Rejects a pending order.
-   **Permissions:** `IsWarehouseAdmin`
-   **Request Body:**
    ```json
    {
        "rejection_reason": "One or more items are out of stock."
    }
    ```

-   **Endpoint:** `/api/warehouse/orders/assign/`
-   **Method:** `POST`
-   **Description:** Assigns a rider to an accepted order.
-   **Permissions:** `IsWarehouseAdmin`
-   **Request Body:**
    ```json
    {
        "order_id": 1,
        "rider_id": 3
    }
    ```

### Rider Management

-   **Endpoint:** `/api/warehouse/riders/`
-   **Method:** `GET`
-   **Description:** Retrieves a list of all riders associated with the warehouse, with optional status filtering.
-   **Permissions:** `IsWarehouseAdmin`
-   **Query Parameters:** `status`
-   **Response:**
    ```json
    [
        {
            "id": 3,
            "user": {
                "full_name": "Jane Doe",
                "email": "jane.doe@example.com"
            },
            "status": "available",
            "availability": "available"
        }
    ]
    ```

-   **Endpoint:** `/api/warehouse/riders/active/`
-   **Method:** `GET`
-   **Description:** Retrieves a list of active riders with their live locations.
-   **Permissions:** `IsWarehouseAdmin`

-   **Endpoint:** `/api/warehouse/riders/metrics/`
-   **Method:** `GET`
-   **Description:** Retrieves performance metrics for all riders in the warehouse.
-   **Permissions:** `IsWarehouseAdmin`

### Analytics

-   **Endpoint:** `/api/warehouses/{id}/analytics/summary/`
-   **Method:** `GET`
-   **Description:** Retrieves a comprehensive analytics summary for the warehouse.
-   **Permissions:** `IsWarehouseAdmin`
-   **Query Parameters:** `from_date`, `to_date`

-   **Endpoint:** `/api/warehouses/{id}/analytics/export/`
-   **Method:** `GET`
-   **Description:** Exports warehouse analytics data in CSV or JSON format.
-   **Permissions:** `IsWarehouseAdmin`
-   **Query Parameters:** `format` (csv or json), `from_date`, `to_date`

---

## Shopkeeper

Shopkeepers can browse nearby warehouses, place orders, track their deliveries, and manage their account.

### Warehouse & Inventory

-   **Endpoint:** `/api/shopkeeper/warehouses/nearby/`
-   **Method:** `GET`
-   **Description:** Finds the nearest warehouse based on the shopkeeper's GPS coordinates.
-   **Permissions:** `IsShopkeeper`
-   **Query Parameters:** `latitude` (required), `longitude` (required), `radius` (optional, default: 10km)
-   **Response:**
    ```json
    {
        "nearest_warehouse": {
            "id": 1,
            "name": "Nearby Warehouse",
            "address": "789 Pine St, Nearburg, USA",
            "distance_km": 2.5
        },
        "total_nearby": 3
    }
    ```

-   **Endpoint:** `/api/shopkeeper/inventory/browse/`
-   **Method:** `GET`
-   **Description:** Browses inventory items from warehouses with filtering options.
-   **Permissions:** `IsShopkeeper`
-   **Query Parameters:** `warehouse`, `search`, `min_price`, `max_price`, `in_stock`
-   **Response:**
    ```json
    [
        {
            "id": 1,
            "name": "Item 1",
            "description": "A high-quality item.",
            "price": "10.00",
            "quantity": 100,
            "warehouse": 1
        }
    ]
    ```

### Order Management

-   **Endpoint:** `/api/shopkeeper/orders/create/`
-   **Method:** `POST`
-   **Description:** Creates a new order from a warehouse.
-   **Permissions:** `IsShopkeeper`
-   **Request Body:**
    ```json
    {
        "warehouse": 1,
        "items": [
            {
                "item_id": 1,
                "quantity": 10
            },
            {
                "item_id": 5,
                "quantity": 2
            }
        ]
    }
    ```

-   **Endpoint:** `/api/shopkeeper/orders/`
-   **Method:** `GET`
-   **Description:** Retrieves a list of all orders placed by the shopkeeper.
-   **Permissions:** `IsShopkeeper`
-   **Query Parameters:** `status`, `ordering`, `start_date`, `end_date`
-   **Response:**
    ```json
    [
        {
            "id": 1,
            "warehouse": 1,
            "status": "delivered",
            "total_amount": "150.75",
            "created_at": "2025-11-06T15:00:00Z"
        }
    ]
    ```

-   **Endpoint:** `/api/shopkeeper/orders/{id}/`
-   **Method:** `GET`
-   **Description:** Retrieves the details of a specific order.
-   **Permissions:** `IsShopkeeper`
-   **Response:**
    ```json
    {
        "id": 1,
        "warehouse": 1,
        "status": "delivered",
        "total_amount": "150.75",
        "order_items": [
            {
                "item": {
                    "name": "Item 1",
                    "price": "10.00"
                },
                "quantity": 15,
                "subtotal": "150.00"
            }
        ],
        "delivery": {
            "rider": 3,
            "status": "delivered"
        }
    }
    ```

-   **Endpoint:** `/api/shopkeeper/orders/{id}/update/`
-   **Method:** `PATCH`
-   **Description:** Cancels a pending order.
-   **Permissions:** `IsShopkeeper`
-   **Request Body:**
    ```json
    {
        "status": "cancelled"
    }
    ```

-   **Endpoint:** `/api/shopkeeper/orders/{id}/tracking/`
-   **Method:** `GET`
-   **Description:** Tracks the current status and rider information for an order.
-   **Permissions:** `IsShopkeeper`
-   **Response:**
    ```json
    {
        "order_id": 1,
        "order_status": "in_transit",
        "order_status_display": "In Transit",
        "rider": {
            "id": 3,
            "phone_number": "+15551234567"
        }
    }
    ```

### Payment Management

-   **Endpoint:** `/api/shopkeeper/payments/`
-   **Method:** `GET`
-   **Description:** Retrieves the payment transaction history for the shopkeeper.
-   **Permissions:** `IsShopkeeper`
-   **Query Parameters:** `status`, `ordering`, `start_date`, `end_date`

-   **Endpoint:** `/api/shopkeeper/payments/summary/`
-   **Method:** `GET`
-   **Description:** Retrieves a summary of payments, including total paid and pending dues.
-   **Permissions:** `IsShopkeeper`

### Notifications

-   **Endpoint:** `/api/shopkeeper/notifications/`
-   **Method:** `GET`
-   **Description:** Retrieves a list of notifications for the shopkeeper.
-   **Permissions:** `IsShopkeeper`
-   **Query Parameters:** `is_read`

-   **Endpoint:** `/api/shopkeeper/notifications/mark-read/`
-   **Method:** `POST`
-   **Description:** Marks one or all notifications as read.
-   **Permissions:** `IsShopkeeper`
-   **Request Body:**
    ```json
    {
        "notification_ids": [1, 2, 3]
    }
    ```

-   **Endpoint:** `/api/shopkeeper/notifications/unread-count/`
-   **Method:** `GET`
-   **Description:** Retrieves the count of unread notifications.
-   **Permissions:** `IsShopkeeper`

### Support

-   **Endpoint:** `/api/shopkeeper/support/tickets/`
-   **Method:** `GET`
-   **Description:** Retrieves a list of support tickets created by the shopkeeper.
-   **Permissions:** `IsShopkeeper`
-   **Query Parameters:** `status`, `category`

-   **Endpoint:** `/api/shopkeeper/support/tickets/create/`
-   **Method:** `POST`
-   **Description:** Creates a new support ticket.
-   **Permissions:** `IsShopkeeper`
-   **Request Body:**
    ```json
    {
        "category": "order_issue",
        "subject": "Problem with my recent order",
        "description": "The items I received were incorrect.",
        "order": 1
    }
    ```

### Analytics

-   **Endpoint:** `/api/shopkeeper/analytics/`
-   **Method:** `GET`
-   **Description:** Retrieves an analytics summary, including spending and order history.
-   **Permissions:** `IsShopkeeper`
-   **Query Parameters:** `months` (default: 6)

---

## Rider

Riders can view assigned orders, update their status, and track their earnings and performance.

### Profile & Availability

-   **Endpoint:** `/api/rider/profile/`
-   **Method:** `GET`
-   **Description:** Retrieves the rider's profile information.
-   **Permissions:** `IsRider`
-   **Response:**
    ```json
    {
        "id": 3,
        "user": {
            "full_name": "Jane Doe",
            "email": "jane.doe@example.com"
        },
        "warehouse": 1,
        "status": "available",
        "availability": "available",
        "total_earnings": "550.25"
    }
    ```

-   **Endpoint:** `/api/rider/profile/`
-   **Method:** `PUT`
-   **Description:** Updates the rider's profile (e.g., status).
-   **Permissions:** `IsRider`
-   **Request Body:**
    ```json
    {
        "status": "on_delivery"
    }
    ```

-   **Endpoint:** `/api/rider/availability/update/`
-   **Method:** `PATCH`
-   **Description:** Toggles the rider's availability status between `available` and `off-duty`.
-   **Permissions:** `IsRider`
-   **Request Body:**
    ```json
    {
        "availability": "off-duty"
    }
    ```

### Order Management

-   **Endpoint:** `/api/rider/orders/`
-   **Method:** `GET`
-   **Description:** Retrieves a list of orders assigned to the rider that are not yet delivered.
-   **Permissions:** `IsRider`

-   **Endpoint:** `/api/rider/orders/update/`
-   **Method:** `PATCH`
-   **Description:** Updates the status of an order (e.g., from `assigned` to `in_transit`, or `in_transit` to `delivered`).
-   **Permissions:** `IsRider`
-   **Request Body:**
    ```json
    {
        "order_id": 1,
        "status": "in_transit"
    }
    ```

### Location Tracking

-   **Endpoint:** `/api/rider/location/update/`
-   **Method:** `PATCH`
-   **Description:** Updates the rider's current GPS location.
-   **Permissions:** `IsRider`
-   **Request Body:**
    ```json
    {
        "latitude": 34.0522,
        "longitude": -118.2437
    }
    ```

### Earnings & Performance

-   **Endpoint:** `/api/rider/earnings/`
-   **Method:** `GET`
-   **Description:** Retrieves a summary of the rider's earnings.
-   **Permissions:** `IsRider`
-   **Query Parameters:** `period` (daily, weekly, monthly), `start_date`, `end_date`

-   **Endpoint:** `/api/rider/history/`
-   **Method:** `GET`
-   **Description:** Retrieves the rider's paginated delivery history.
-   **Permissions:** `IsRider`

-   **Endpoint:** `/api/rider/performance/`
-   **Method:** `GET`
-   **Description:** Retrieves the rider's performance metrics.
-   **Permissions:** `IsRider`

### Notifications

-   **Endpoint:** `/api/rider/notifications/`
-   **Method:** `GET`
-   **Description:** Retrieves a list of notifications for the rider.
-   **Permissions:** `IsRider`
-   **Query Parameters:** `is_read`

-   **Endpoint:** `/api/rider/notifications/{id}/mark-read/`
-   **Method:** `PATCH`
-   **Description:** Marks a specific notification as read.
-   **Permissions:** `IsRider`
