# Orders App API Documentation

## Purpose
- Core endpoints for shopkeepers to create orders and list their orders.
- For advanced customer features (tracking, updates, analytics), use the Shopkeepers module.

## Base URL
- /orders/

## Authentication
- Token required: `Authorization: Token <token>`
- Role: `SHOPKEEPER`

## Endpoints

### 1) Create Order
- **POST** `/orders/create/`
- **Body**:
  ```json
  {
    "warehouse": 1,
    "items": [
      { "item": 5, "quantity": 10 },
      { "item": 8, "quantity": 2 }
    ]
  }
  ```
- **201 Created**: OrderSerializer payload
- **Errors**: 400 on invalid warehouse/items or insufficient stock

### 2) List My Orders
- **GET** `/orders/`
- **200 OK**: `[ OrderSerializer, ... ]`

## Schemas
- **OrderSerializer** fields: `id`, `shopkeeper`, `warehouse`, `status`, `total_amount`, `order_items[]`, `created_at`, `updated_at`
- **OrderItem** fields: `id`, `order`, `item`, `item_name`, `quantity`, `price`

## Notes
- This app provides the minimal order flows; the customer-facing endpoints with filters, pagination, tracking, and cancellations are under `/shopkeeper/`.
