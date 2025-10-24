# Inventory App API Documentation

## Purpose
- Manage inventory items for a specific warehouse.

## Base URLs
- `/warehouse/<warehouse_id>/items/`
- `/warehouse/<warehouse_id>/items/<item_id>/`

## Authentication
- Token required: `Authorization: Token <token>`
- Roles: `WAREHOUSE_ADMIN` for the warehouse or `SUPER_ADMIN`

## Endpoints

### 1. List & Create Items
- **GET** `/warehouse/{warehouse_id}/items/`
  - List items for the warehouse (most recent first)
  - **Response 200 OK**: 
    ```json
    {
      "count": ...,
      "next": ...,
      "previous": ...,
      "results": [ { item fields... } ]
    }
    ```
- **POST** `/warehouse/{warehouse_id}/items/`
  - Create a new item in the warehouse
  - **Request Body**:
    ```json
    {
      "name": "Rice 5kg",
      "description": "Premium",
      "sku": "RICE-5KG",
      "price": "100.00",
      "quantity": 100
    }
    ```
  - **Response 201 Created**: created item

### 2. Retrieve & Update Item
- **GET** `/warehouse/{warehouse_id}/items/{item_id}/`
  - Retrieve details for a single item
- **PATCH** `/warehouse/{warehouse_id}/items/{item_id}/`
- **PUT** `/warehouse/{warehouse_id}/items/{item_id}/`
  - Update item (quantity, price, etc.)

## Item Schema (ItemSerializer)
- Fields: `id`, `warehouse`, `name`, `description`, `sku`, `price`, `quantity`, `available`, `created_at`, `updated_at`
- Notes: quantity must be non-negative

## Permissions
- Object-level checks ensure only the owning warehouse admin (or super admin) can manage items.
- Super admins may act on any warehouse.

## Errors
- 404 if warehouse not found or user lacks access
- 400 on validation errors
