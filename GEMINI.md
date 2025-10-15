# GEMINI - Rural Supply & Delivery Backend MVP Guide

## Project Overview

GEMINI is a modular monolithic backend built with Django and Django REST Framework (DRF). It caters to rural shopkeepers seeking nearby warehouses, managing orders, warehouse inventory, riders, and payments. Authentication is handled via OTP. The MVP is API-based only.

### Core Features

* Shopkeeper: order items from nearby warehouses.
* Warehouse: manage inventory, accept/reject orders.
* Rider: get assigned orders, track deliveries, receive payments.
* Admin: manage users, warehouses, inventory, and payouts.
* OTP-based authentication.
* Payment calculation based on delivery distance.

## Technology Stack

* **Backend:** Django + Django REST Framework
* **Database:** PostgreSQL (PostGIS optional for geolocation queries)
* **Cache/Queue:** Redis (OTP storage, caching, async tasks)
* **Authentication:** OTP via mobile number, DRF token or JWT for session management
* **SMS Providers (Free/Low-Cost):** Fast2SMS, MSG91
* **Deployment:** Dockerized, deployable on Render, Railway, or AWS EC2

## Project Structure

```
.
├── accounts
│   ├── admin.py
│   ├── apps.py
│   ├── __init__.py
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   └── __init__.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── backend
│   ├── asgi.py
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── configs
│   └── config.py
├── delivery
│   ├── admin.py
│   ├── apps.py
│   ├── __init__.py
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   └── __init__.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   └── views.py
├── GEMINI.md
├── inventory
│   ├── admin.py
│   ├── apps.py
│   ├── __init__.py
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   └── __init__.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   └── views.py
├── manage.py
├── orders
│   ├── admin.py
│   ├── apps.py
│   ├── __init__.py
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   └── __init__.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   └── views.py
├── payments
│   ├── admin.py
│   ├── apps.py
│   ├── __init__.py
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   └── __init__.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   └── views.py
├── plans.md
├── pyproject.toml
├── requirements.txt
├── uv.lock
├── warehouses
│   ├── admin.py
│   ├── apps.py
│   ├── __init__.py
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   └── __init__.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   └── views.py
└── WARP.md -> GEMINI.md

```

## MVP Roadmap

### Phase 0: Foundations

1. Initialize Django project with DRF.
2. Configure PostgreSQL and Redis.
3. Set up project structure with modular apps.

### Phase 1: Users & Authentication

1. Implement roles: shopkeeper, warehouse_admin, rider, super_admin.
2. OTP-based login:

    * `/auth/request-otp/`: generate OTP, store in Redis, send via SMS.
    * `/auth/verify-otp/`: validate OTP, issue DRF token/JWT.
3. Basic profile APIs per role.

### Phase 2: Warehouse & Inventory

1. Warehouse model with name, location, admin.
2. Item model: stock, SKU, price, warehouse FK.
3. APIs:

    * Warehouse CRUD
    * Inventory CRUD & stock updates
    * Item search per warehouse (optional)

### Phase 3: Orders

1. Order model: shopkeeper → warehouse, items, quantity, status.
2. APIs:

    * Shopkeeper: create order, view status
    * Warehouse: accept/reject orders
3. Validate inventory before order acceptance.

### Phase 4: Rider Management & Delivery

1. Rider model linked to warehouse, status tracking.
2. Assign nearest/available rider on order acceptance.
3. Calculate delivery distance & payment (PostGIS or haversine formula).
4. APIs:

    * Rider: view assigned orders, update delivery status
    * Warehouse: track rider assignments

### Phase 5: Payments & Admin

1. Payment model: rider payouts, warehouse settlements.
2. Admin APIs:

    * Manage users, warehouses, inventory, orders
    * View payouts
3. Super_admin dashboard via Django admin.

### Phase 6: Enhancements

1. Caching with Redis for frequent queries.
2. Swagger/OpenAPI documentation via `drf-spectacular`.
3. Rate-limiting OTP endpoints.
4. Logging, error handling, notifications.

### Phase 7: Deployment

1. Dockerize backend.
2. Deploy backend + PostgreSQL + Redis.
3. Integrate with mobile app for OTP, order workflow, and rider tracking.

## Notes & Best Practices

* Keep OTP stateless using Redis for auto-expiry.
* Use PostGIS for geolocation queries if nearest-warehouse search is frequent.
* Ensure proper indexing on orders, warehouses, and riders.
* Maintain modularity for easier future scaling and feature addition.
* Use DRF permissions to enforce role-based access.

This structure enables rapid MVP development while keeping the system maintainable and ready for future scaling.
