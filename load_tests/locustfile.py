"""
load_tests/locustfile.py
--------------------------
Main Locust entrypoint.  Defines one HttpUser subclass per role.

User class weights are read from config.py and respect the realistic
production traffic mix (shopkeepers dominate, riders are chatty due to
location pings, warehouse managers are mid-tier, admins are rare).

Auth flow (shared by all roles):
  1. on_start() calls do_login() which POSTs to /api/accounts/signin/
  2. The Supabase-issued JWT access_token is injected into
     client.headers["Authorization"] = "Bearer <token>"
  3. All subsequent task requests inherit this header automatically.

Run headless:
  uv run locust -f load_tests/locustfile.py \\
      --headless -u 20 -r 4 --run-time 60s \\
      --host=http://localhost:8000 \\
      --csv=load_tests/results

Run with web UI:
  uv run locust -f load_tests/locustfile.py --host=http://localhost:8000
"""

import sys
import os

# Allow `from load_tests.xxx import yyy` when running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from locust import HttpUser, between, events

import load_tests.config as cfg
from load_tests.tasks.auth_tasks import do_login
from load_tests.tasks.shopkeeper_tasks import ShopkeeperBrowseTasks
from load_tests.tasks.order_tasks import ShopkeeperOrderTasks, WarehouseOrderTasks
from load_tests.tasks.inventory_tasks import InventoryReadTasks, InventoryWriteTasks
from load_tests.tasks.rider_tasks import RiderTaskSet, WarehouseRiderManagementTasks
from load_tests.tasks.warehouse_tasks import WarehouseManagementTasks
from load_tests.tasks.admin_tasks import AdminTaskSet


# ---------------------------------------------------------------------------
# Shopkeeper User
# ---------------------------------------------------------------------------
class ShopkeeperUser(HttpUser):
    """
    Simulates a logged-in shopkeeper.
    Traffic mix: heavy reads (browse/orders/notifications), light writes (order creation).
    """
    weight = cfg.SHOPKEEPER_WEIGHT
    wait_time = between(cfg.MIN_WAIT, cfg.MAX_WAIT)
    tasks = {
        ShopkeeperBrowseTasks: 8,
        ShopkeeperOrderTasks: 4,
    }

    def on_start(self):
        token = do_login(self.client, cfg.SHOPKEEPER_EMAIL, cfg.SHOPKEEPER_PASSWORD)
        if not token:
            self.environment.runner.quit()

        # Discover a warehouse ID and item ID for use in write tasks
        with self.client.get(
            "/api/shopkeepers/warehouses/nearby/?latitude=28.6139&longitude=77.2090",
            catch_response=True,
            name="INIT | shopkeeper discover warehouses",
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                items = data if isinstance(data, list) else data.get("results", [])
                if items:
                    self.warehouse_id = items[0].get("id", cfg.DEFAULT_WAREHOUSE_ID)
                else:
                    self.warehouse_id = cfg.DEFAULT_WAREHOUSE_ID
                resp.success()
            else:
                self.warehouse_id = cfg.DEFAULT_WAREHOUSE_ID
                resp.success()  # Don't fail init on empty DB

        # Discover a browsable item ID
        with self.client.get(
            "/api/shopkeepers/inventory/browse/",
            catch_response=True,
            name="INIT | shopkeeper discover items",
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                items = data if isinstance(data, list) else data.get("results", [])
                if items:
                    self.sample_item_id = items[0].get("id", cfg.DEFAULT_ITEM_ID)
                else:
                    self.sample_item_id = cfg.DEFAULT_ITEM_ID
                resp.success()
            else:
                self.sample_item_id = cfg.DEFAULT_ITEM_ID
                resp.success()

        self.sample_order_id = None


# ---------------------------------------------------------------------------
# Warehouse Manager User
# ---------------------------------------------------------------------------
class WarehouseManagerUser(HttpUser):
    """
    Simulates a warehouse manager: managing orders, inventory, riders, analytics.
    """
    weight = cfg.WAREHOUSE_WEIGHT
    wait_time = between(cfg.MIN_WAIT, cfg.MAX_WAIT)
    tasks = {
        WarehouseManagementTasks: 6,
        WarehouseOrderTasks: 5,
        InventoryReadTasks: 4,
        InventoryWriteTasks: 2,
        WarehouseRiderManagementTasks: 3,
    }

    def on_start(self):
        token = do_login(self.client, cfg.WAREHOUSE_EMAIL, cfg.WAREHOUSE_PASSWORD)
        if not token:
            self.environment.runner.quit()

        # Discover managed warehouse
        self.warehouse_id = cfg.DEFAULT_WAREHOUSE_ID
        self.sample_order_id = None
        self.sample_item_id = cfg.DEFAULT_ITEM_ID
        self.sample_rider_id = None
        self.pending_order_id = None

        with self.client.get(
            "/api/warehouses/",
            catch_response=True,
            name="INIT | warehouse manager discover warehouse",
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                items = data if isinstance(data, list) else data.get("results", [])
                if items:
                    self.warehouse_id = items[0].get("id", cfg.DEFAULT_WAREHOUSE_ID)
                resp.success()
            else:
                resp.success()


# ---------------------------------------------------------------------------
# Rider User
# ---------------------------------------------------------------------------
class RiderUser(HttpUser):
    """
    Simulates an active rider: high-frequency location pings + order status updates.
    """
    weight = cfg.RIDER_WEIGHT
    wait_time = between(cfg.MIN_WAIT, cfg.MAX_WAIT)
    tasks = {RiderTaskSet: 1}

    def on_start(self):
        token = do_login(self.client, cfg.RIDER_EMAIL, cfg.RIDER_PASSWORD)
        if not token:
            self.environment.runner.quit()

        self.rider_order_id = None


# ---------------------------------------------------------------------------
# Admin User
# ---------------------------------------------------------------------------
class AdminUser(HttpUser):
    """
    Simulates an admin/super-admin user: user management, analytics, payout oversight.
    Very low spawn weight – admins are rare in production.
    """
    weight = cfg.ADMIN_WEIGHT
    wait_time = between(cfg.MIN_WAIT, cfg.MAX_WAIT)
    tasks = {AdminTaskSet: 1}

    def on_start(self):
        token = do_login(self.client, cfg.ADMIN_EMAIL, cfg.ADMIN_PASSWORD)
        if not token:
            self.environment.runner.quit()

        self.sample_user_id = None


# ---------------------------------------------------------------------------
# Hook: print a summary note about credential requirements on startup
# ---------------------------------------------------------------------------
@events.init.add_listener
def on_locust_init(environment, **kwargs):
    print(
        "\n[Stockway Load Tests] Ensure pre-seeded test accounts exist:\n"
        f"  SHOPKEEPER    : {cfg.SHOPKEEPER_EMAIL}\n"
        f"  WAREHOUSE_MGR : {cfg.WAREHOUSE_EMAIL}\n"
        f"  RIDER         : {cfg.RIDER_EMAIL}\n"
        f"  ADMIN         : {cfg.ADMIN_EMAIL}\n"
        "Override any credential via env var (see load_tests/config.py).\n"
    )
