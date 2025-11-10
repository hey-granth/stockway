# Payments and Settlements System API Documentation

## Purpose
Complete payment and settlement system for tracking:
- Payments from shopkeepers to warehouses for orders
- Payouts from warehouses to riders for deliveries
- Automated payout computation and settlement via Celery

## Architecture
- **Models**: Payment (shopkeeper→warehouse), Payout (warehouse→rider)
- **Backend**: Django REST Framework with atomic transactions
- **Queue**: RabbitMQ (AMQP) for task routing
- **Cache/Results**: Redis for Celery results
- **Automation**: Celery Beat for nightly payout rollups

---

## Payment Endpoints

### 1. Initiate Payment
**POST** `/api/payments/initiate/`

Shopkeeper creates payment for an order.

**Authentication**: Required (Shopkeeper only)

**Request Body**:
```json
{
  "order_id": 123,
  "amount": 1200.50,
  "mode": "upi"
}
```

**Validations**:
- Payment amount must equal order total
- No duplicate payments for same order
- Order must belong to requesting shopkeeper

**Response** (201 Created):
```json
{
  "payment_id": 456,
  "order_id": 123,
  "status": "pending",
  "amount": 1200.50,
  "mode": "upi",
  "timestamp": "2025-11-09T12:45:00Z"
}
```

**Payment Modes**: `upi`, `cash`, `credit`

---

### 2. Confirm/Reject Payment
**PATCH** `/api/payments/confirm/`

Warehouse admin confirms or rejects payment.

**Authentication**: Required (Warehouse Manager or Admin only)

**Request Body**:
```json
{
  "payment_id": 456,
  "action": "confirm"
}
```

**Actions**: `confirm` (completes payment), `reject` (marks as failed)

**Permissions**:
- Warehouse managers can only confirm payments for their warehouse
- Admins can confirm any payment

**Response** (200 OK):
```json
{
  "payment_id": 456,
  "order_id": 123,
  "status": "completed",
  "amount": 1200.50,
  "mode": "upi",
  "timestamp": "2025-11-09T12:45:00Z"
}
```

---

## Payout Endpoints

### 3. Process Payouts
**POST** `/api/payments/payouts/process/`

Admin or automated task computes payouts for delivered orders.

**Authentication**: Required (Warehouse Manager or Admin only)

**Request Body** (all fields optional):
```json
{
  "order_ids": [101, 102, 103],
  "rate_per_km": 10.00
}
```

**Behavior**:
- If `order_ids` provided: processes those specific orders
- If omitted: processes ALL delivered orders
- Warehouse managers only process payouts for their warehouse
- Calculates distance from delivery records (PostGIS)
- Creates or updates payout records

**Response** (201 Created):
```json
{
  "success": true,
  "payouts_created": 3,
  "payouts": [
    {
      "payout_id": 789,
      "order_id": 101,
      "rider_id": 55,
      "amount": 125.50
    }
  ],
  "errors": []
}
```

---

### 4. List Payouts
**GET** `/api/payments/payouts/list/`

View payout summaries filtered by user role.

**Authentication**: Required

**Query Parameters**:
- `status` (optional): Filter by status (`pending`, `settled`)

**Permissions**:
- **Riders**: See only their own payouts
- **Warehouse Managers**: See payouts for their warehouse
- **Admins**: See all payouts

**Response** (200 OK):
```json
[
  {
    "payout_id": 789,
    "rider_id": 55,
    "warehouse_id": 12,
    "total_distance": 15.5,
    "rate_per_km": 10.00,
    "computed_amount": 155.00,
    "status": "pending",
    "timestamp": "2025-11-09T14:30:00Z"
  }
]
```

---

## Celery Tasks

### Background Tasks (Automatic)

#### `payouts.compute_for_order`
- **Trigger**: After delivery completion
- **Queue**: `payments`
- **Function**: Computes payout for single delivered order
- **Retry**: 3 attempts with exponential backoff

#### `payouts.nightly_rollup`
- **Schedule**: Daily (configurable in Celery Beat)
- **Queue**: `payments`
- **Function**: Aggregates all pending payouts per warehouse, marks as settled
- **Output**: Settlement summary sent to warehouse admins

#### `payouts.notify_completion`
- **Queue**: `notifications`
- **Function**: Sends notification on payout success/failure
- **Integration**: Uses `notifications` app queue

#### `payouts.notify_creation`
- **Queue**: `notifications`
- **Function**: Notifies rider when payout is created

#### `payouts.notify_settlement`
- **Queue**: `notifications`
- **Function**: Notifies warehouse admin on daily settlement

---

## Models

### Payment
| Field | Type | Description |
|-------|------|-------------|
| order | FK | Order being paid for |
| payer | FK | Shopkeeper making payment |
| payee | FK | Warehouse admin receiving payment |
| amount | Decimal | Payment amount |
| mode | Choice | `upi`, `cash`, `credit` |
| status | Choice | `pending`, `completed`, `failed` |
| created_at | DateTime | Auto-generated |
| updated_at | DateTime | Auto-updated |

**Constraints**: `unique_together(order, payer)` - prevents duplicate payments

### Payout
| Field | Type | Description |
|-------|------|-------------|
| rider | FK | Rider receiving payout |
| warehouse | FK | Warehouse processing payout |
| total_distance | Float | Distance in kilometers |
| rate_per_km | Decimal | Rate per kilometer |
| computed_amount | Decimal | Calculated payout amount |
| status | Choice | `pending`, `settled` |
| created_at | DateTime | Auto-generated |
| updated_at | DateTime | Auto-updated |

---

## Business Logic

### Payment Workflow
1. Shopkeeper initiates payment after order confirmation
2. System validates amount equals order total
3. Payment created with `pending` status
4. Warehouse admin reviews and confirms/rejects
5. On confirmation: status → `completed`
6. On rejection: status → `failed`

### Payout Workflow
1. Delivery marked as `delivered`
2. Celery task `compute_for_order` triggered
3. System retrieves delivery distance (PostGIS)
4. Computes: `amount = distance × rate_per_km`
5. Creates Payout record with `pending` status
6. Nightly rollup aggregates all pending payouts
7. Marks as `settled`, notifies warehouse and riders

### Distance Calculation
- Primary: `delivery.distance_km` field
- Fallback: PostGIS distance calculation from pickup/delivery locations
- Default: 0.0 km if unavailable

---

## Error Responses

**403 Forbidden** - Insufficient permissions
```json
{
  "error": "Only shopkeepers can initiate payments."
}
```

**400 Bad Request** - Validation error
```json
{
  "amount": ["Payment amount must equal order total: 1200.50"]
}
```

**404 Not Found** - Resource not found
```json
{
  "error": "Payment not found."
}
```

---

## Security & Constraints

- All endpoints require authentication
- Role-based access control enforced
- Atomic database transactions prevent inconsistencies
- Payment amount must match order total (validated)
- Unique constraint prevents duplicate payments
- Query optimization with `select_related()`

---

## Integration

### RabbitMQ Queues
- `payments`: Payment/payout processing tasks
- `notifications`: Notification delivery tasks

### Redis
- Stores Celery task results
- Backend: `redis://127.0.0.1:6379/0`

### Celery Beat Schedule
```python
CELERY_BEAT_SCHEDULE = {
    "nightly-payout-rollup": {
        "task": "payouts.nightly_rollup",
        "schedule": 86400.0,  # Daily
    }
}
```
- `payer` and `payee` are ForeignKeys to User model
- `order` is optional ForeignKey to Order model
- `warehouse` is optional ForeignKey to Warehouse model

## Permissions
- Shopkeepers can view their own payments
- Warehouse admins can view payments related to their warehouse
- Super admins can view all payments
- Role-based access control for payment creation and updates


