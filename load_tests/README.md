# Stockway Load Tests — Locust

End-to-end HTTP load testing for the Stockway Django/DRF backend.
Tests are isolated in `load_tests/` and **do not modify any existing project file**.

---

## Prerequisites

```bash
# Locust is installed as a dev dependency via uv
uv sync
```

---

## Configuration

All settings live in `load_tests/config.py` and are overridable via env vars:

| Env Var | Default | Description |
|---|---|---|
| `LOCUST_HOST` | `http://localhost:8000` | Target host |
| `LOCUST_MIN_WAIT` | `1` | Minimum think time (seconds) |
| `LOCUST_MAX_WAIT` | `3` | Maximum think time (seconds) |
| `LOCUST_SHOPKEEPER_EMAIL` | `shopkeeper@test.local` | Shopkeeper test account |
| `LOCUST_SHOPKEEPER_PASSWORD` | `Test1234!` | |
| `LOCUST_WAREHOUSE_EMAIL` | `warehouse@test.local` | Warehouse manager test account |
| `LOCUST_WAREHOUSE_PASSWORD` | `Test1234!` | |
| `LOCUST_RIDER_EMAIL` | `rider@test.local` | Rider test account |
| `LOCUST_RIDER_PASSWORD` | `Test1234!` | |
| `LOCUST_ADMIN_EMAIL` | `admin@test.local` | Admin test account |
| `LOCUST_ADMIN_PASSWORD` | `Test1234!` | |
| `LOCUST_DEFAULT_WAREHOUSE_ID` | `1` | Fallback warehouse ID |
| `LOCUST_DEFAULT_ITEM_ID` | `1` | Fallback item ID |

---

## Account Setup (required before running)

The suite requires **four pre-seeded Supabase accounts** in the target DB,
one per role (`SHOPKEEPER`, `WAREHOUSE_MANAGER`, `RIDER`, `ADMIN`).

```bash
# Example: seed via Django shell
python manage.py shell -c "
from accounts.models import User
# Create if not exists, then set role
for email, role in [
    ('shopkeeper@test.local', 'SHOPKEEPER'),
    ('warehouse@test.local',  'WAREHOUSE_MANAGER'),
    ('rider@test.local',      'RIDER'),
    ('admin@test.local',      'ADMIN'),
]:
    u, _ = User.objects.get_or_create(email=email, defaults={'role': role})
    u.role = role; u.save()
    print(f'OK: {email} → {role}')
"
```

> The accounts must also exist in **Supabase Auth** (sign-up them first via
> `POST /api/accounts/signup/`) since this project uses Supabase JWTs.

---

## Running — Headless (CI / terminal)

```bash
# Basic smoke test (10 users, ramp 2/s, 30 seconds, all roles)
uv run locust -f load_tests/locustfile.py \
    --headless -u 10 -r 2 --run-time 30s \
    --host=http://localhost:8000 \
    --csv=load_tests/results

# Full soak test (100 users)
uv run locust -f load_tests/locustfile.py \
    --headless -u 100 -r 10 --run-time 5m \
    --host=http://localhost:8000 \
    --csv=load_tests/results

# Against production (read-only, low load)
LOCUST_SHOPKEEPER_EMAIL=sk@prod.example LOCUST_SHOPKEEPER_PASSWORD=SecurePass \
uv run locust -f load_tests/locustfile.py \
    --headless -u 5 -r 1 --run-time 60s \
    --host=https://stockway.onrender.com \
    --csv=load_tests/results_prod \
    --only-summary

# Single role (just shopkeeper)
uv run locust -f load_tests/locustfile.py \
    --headless -u 20 -r 4 --run-time 2m \
    --host=http://localhost:8000 \
    --csv=load_tests/results_shopkeeper \
    --class-picker  # interactive selection in web UI
```

### CSV Output Files
`--csv=load_tests/results` writes:
- `load_tests/results_stats.csv` — per-endpoint stats
- `load_tests/results_stats_history.csv` — time-series
- `load_tests/results_failures.csv` — failure details
- `load_tests/results_exceptions.csv` — exception traces

---

## Running — Web UI

```bash
uv run locust -f load_tests/locustfile.py --host=http://localhost:8000
# Open http://localhost:8089 in browser
```

---

## File Structure

```
load_tests/
├── locustfile.py          # Main entrypoint; one HttpUser per role
├── config.py              # Host, credentials, wait times (all env-overridable)
├── README.md              # This file
└── tasks/
    ├── auth_tasks.py      # Shared login helper + CurrentUser task set
    ├── shopkeeper_tasks.py # Browse, notifications, payments, support tickets
    ├── order_tasks.py      # Order create/list/accept/reject/assign
    ├── inventory_tasks.py  # Item list/create/update
    ├── rider_tasks.py      # Location pings, order status, availability
    ├── warehouse_tasks.py  # Warehouse CRUD, analytics, payouts
    └── admin_tasks.py      # User management, rider admin, analytics (admin role)
```

---

## User Roles & Weights

| User Class | Weight | Task Sets |
|---|---|---|
| `ShopkeeperUser` | 6 | Browse (8), Orders (4) |
| `WarehouseManagerUser` | 3 | Warehouse mgmt (6), Orders (5), Inventory read (4), Inventory write (2), Rider mgmt (3) |
| `RiderUser` | 2 | Location pings (high), order updates, availability |
| `AdminUser` | 1 | User list/detail, rider admin, payouts |

At `-u 10`, expect roughly: 5 shopkeepers, 2 warehouse managers, 2 riders, 1 admin.

---

## Known Gaps

The following endpoints could not have their full payload determined from the
codebase alone and are either excluded or hit with minimal payloads:

1. **`POST /api/inventory/warehouses/{id}/items/{id}/images/`** — requires
   `multipart/form-data` with binary image files. Locust can send these but
   generating realistic test images at load-test scale is non-trivial.
   Excluded from the suite; test manually with a static fixture image.

2. **`POST /api/payments/initiate/`** — `PaymentInitiateSerializer` validates
   that `amount` exactly matches `order.total_amount`. This requires a
   live order ID with a known amount, making it fragile under parallel load.
   The task is excluded; test the payment flow as an integration test instead.

3. **`POST /api/payments/confirm/`** — requires a `payment_id` in `pending`
   state and a warehouse manager caller that owns the related order's warehouse.
   Excluded for the same reason.

4. **`POST /api/warehouses/{pk}/inventory/bulk-update/`** — view file shows
   this action exists but the serializer/payload shape is defined inline in
   the view. Without a clear serializer export, this is excluded to avoid
   sending malformed payloads.

5. **`GET /api/analytics/system/` and `/api/analytics/warehouse/`** — these
   are custom `@action` methods on `AnalyticsViewSet`. The exact sub-URL paths
   depend on the DRF router (typically `/api/analytics/system/` and
   `/api/analytics/warehouse/`). If they return 404, check the router-generated
   URL list with `python manage.py show_urls | grep analytics`.
