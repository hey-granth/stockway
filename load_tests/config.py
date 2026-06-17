"""
load_tests/config.py
--------------------
Centralised configuration for all Locust task sets.
All values can be overridden via environment variables so the same
suite works locally and in CI without touching code.

Usage:
    HOST=https://stockway.onrender.com locust -f load_tests/locustfile.py ...
"""

import os

# ---------------------------------------------------------------------------
# Target host
# ---------------------------------------------------------------------------
HOST = os.getenv("LOCUST_HOST", "http://localhost:8000")

# ---------------------------------------------------------------------------
# Wait time bounds (seconds) – used as between(MIN_WAIT, MAX_WAIT)
# ---------------------------------------------------------------------------
MIN_WAIT = float(os.getenv("LOCUST_MIN_WAIT", "1"))
MAX_WAIT = float(os.getenv("LOCUST_MAX_WAIT", "3"))

# ---------------------------------------------------------------------------
# Role credentials
# Each role must correspond to a real, pre-seeded account in the target DB.
# Override via env vars before running; do NOT commit real passwords.
# ---------------------------------------------------------------------------
SHOPKEEPER_EMAIL = os.getenv("LOCUST_SHOPKEEPER_EMAIL", "shopkeeper@test.local")
SHOPKEEPER_PASSWORD = os.getenv("LOCUST_SHOPKEEPER_PASSWORD", "Test1234!")

WAREHOUSE_EMAIL = os.getenv("LOCUST_WAREHOUSE_EMAIL", "warehouse@test.local")
WAREHOUSE_PASSWORD = os.getenv("LOCUST_WAREHOUSE_PASSWORD", "Test1234!")

RIDER_EMAIL = os.getenv("LOCUST_RIDER_EMAIL", "rider@test.local")
RIDER_PASSWORD = os.getenv("LOCUST_RIDER_PASSWORD", "Test1234!")

ADMIN_EMAIL = os.getenv("LOCUST_ADMIN_EMAIL", "admin@test.local")
ADMIN_PASSWORD = os.getenv("LOCUST_ADMIN_PASSWORD", "Test1234!")

# ---------------------------------------------------------------------------
# Seed IDs – replaced at runtime via on_start discovery, but kept here
# as fallback defaults for smoke-test mode when the DB has pre-seeded rows.
# ---------------------------------------------------------------------------
DEFAULT_WAREHOUSE_ID = int(os.getenv("LOCUST_DEFAULT_WAREHOUSE_ID", "1"))
DEFAULT_ITEM_ID = int(os.getenv("LOCUST_DEFAULT_ITEM_ID", "1"))

# ---------------------------------------------------------------------------
# Locust spawn weights per role (used in locustfile.py)
# Reflect a realistic production traffic mix:
#   shopkeeper read/browse >> warehouse ops >> rider pings >> admin
# ---------------------------------------------------------------------------
SHOPKEEPER_WEIGHT = int(os.getenv("LOCUST_SHOPKEEPER_WEIGHT", "6"))
WAREHOUSE_WEIGHT = int(os.getenv("LOCUST_WAREHOUSE_WEIGHT", "3"))
RIDER_WEIGHT = int(os.getenv("LOCUST_RIDER_WEIGHT", "2"))
ADMIN_WEIGHT = int(os.getenv("LOCUST_ADMIN_WEIGHT", "1"))

# ---------------------------------------------------------------------------
# Auth endpoint (shared across all roles)
# ---------------------------------------------------------------------------
SIGNIN_ENDPOINT = "/api/accounts/signin/"
