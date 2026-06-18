"""
load_tests/tasks/inventory_tasks.py
-------------------------------------
Task sets for the Inventory domain.

Endpoints covered:
  GET  /api/inventory/warehouses/{id}/items/          (list)
  GET  /api/inventory/warehouses/{id}/items/{pk}/     (detail)
  POST /api/inventory/warehouses/{id}/items/          (create – warehouse role)
  PUT  /api/inventory/warehouses/{id}/items/{pk}/     (update – warehouse role)

Access control (from codebase):
  ItemListCreateView  – IsAuthenticated + IsWarehouseAdminOrSuperAdmin
  ItemDetailView      – IsAuthenticated + IsWarehouseAdminOrSuperAdmin

Shopkeepers browse inventory through the separate shopkeeper API:
  GET  /api/shopkeeper/inventory/browse/
These are handled in shopkeeper_tasks.py.
"""

import random
from locust import TaskSet, task

from load_tests.config import DEFAULT_WAREHOUSE_ID


# ---------------------------------------------------------------------------
# Read-heavy task set – used by Warehouse role users
# ---------------------------------------------------------------------------
class InventoryReadTasks(TaskSet):
    """
    Read-only inventory tasks (high weight – inventory browsing is frequent).
    Requires: warehouse_id stored in self.user.warehouse_id by on_start.
    """

    @task(10)
    def list_items(self):
        wid = getattr(self.user, "warehouse_id", DEFAULT_WAREHOUSE_ID)
        with self.client.get(
            f"/api/inventory/warehouses/{wid}/items/",
            catch_response=True,
            name="INVENTORY | GET items list",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"list items → HTTP {resp.status_code}: {resp.text[:200]}")

    @task(5)
    def get_item_detail(self):
        wid = getattr(self.user, "warehouse_id", DEFAULT_WAREHOUSE_ID)
        item_id = getattr(self.user, "sample_item_id", 1)
        with self.client.get(
            f"/api/inventory/warehouses/{wid}/items/{item_id}/",
            catch_response=True,
            name="INVENTORY | GET item detail",
        ) as resp:
            if resp.status_code in (200, 404):
                # 404 is acceptable – item may not exist yet in test DB
                resp.success()
            else:
                resp.failure(
                    f"item detail → HTTP {resp.status_code}: {resp.text[:200]}"
                )


class InventoryWriteTasks(TaskSet):
    """
    Write tasks for warehouse managers: create and update items.
    Low weight – writes are far less frequent than reads.
    """

    @task(3)
    def create_item(self):
        wid = getattr(self.user, "warehouse_id", DEFAULT_WAREHOUSE_ID)
        sku = f"SKU-LOAD-{random.randint(10000, 99999)}"
        payload = {
            "name": f"Load Test Item {random.randint(1, 1000)}",
            "sku": sku,
            "description": "Created by Locust load test",
            "category": "test",
            "price": str(round(random.uniform(10.0, 500.0), 2)),
            "quantity": random.randint(5, 200),
        }
        with self.client.post(
            f"/api/inventory/warehouses/{wid}/items/",
            json=payload,
            catch_response=True,
            name="INVENTORY | POST create item",
        ) as resp:
            if resp.status_code == 201:
                # Cache the new item_id for subsequent detail/update tasks
                created_id = resp.json().get("id")
                if created_id:
                    self.user.sample_item_id = created_id
                resp.success()
            elif resp.status_code == 400:
                # Duplicate SKU from parallel workers — expected under load
                resp.success()
            else:
                resp.failure(
                    f"create item → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(2)
    def update_item(self):
        wid = getattr(self.user, "warehouse_id", DEFAULT_WAREHOUSE_ID)
        item_id = getattr(self.user, "sample_item_id", 1)
        payload = {
            "quantity": random.randint(1, 100),
            "price": str(round(random.uniform(10.0, 500.0), 2)),
        }
        with self.client.patch(
            f"/api/inventory/warehouses/{wid}/items/{item_id}/",
            json=payload,
            catch_response=True,
            name="INVENTORY | PATCH update item",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(
                    f"update item → HTTP {resp.status_code}: {resp.text[:200]}"
                )
