"""
load_tests/tasks/warehouse_tasks.py
-------------------------------------
Task sets specific to the Warehouse Manager role beyond orders.

Warehouse ViewSet endpoints (DefaultRouter → /api/warehouses/):
  GET    /api/warehouses/                          list
  POST   /api/warehouses/                          create
  GET    /api/warehouses/{pk}/                     retrieve
  PUT    /api/warehouses/{pk}/                     update
  GET    /api/warehouses/{pk}/inventory/           custom action
  POST   /api/warehouses/{pk}/inventory/bulk-update/
  GET    /api/warehouses/{pk}/orders/              custom action
  GET    /api/warehouses/{pk}/deliveries/          custom action
  GET    /api/warehouses/{pk}/notifications/       custom action
  POST   /api/warehouses/{pk}/notifications/mark-read/
  GET    /api/warehouses/{pk}/rider-payouts/       custom action
  GET    /api/warehouses/{pk}/analytics/summary/   custom action
  GET    /api/warehouses/{pk}/analytics/export/    custom action

Analytics ViewSet (ReadOnly → /api/analytics/):
  GET  /api/analytics/

Payments:
  GET  /api/payments/payouts/list/
"""

import random
from locust import TaskSet, task

from load_tests.config import DEFAULT_WAREHOUSE_ID


class WarehouseManagementTasks(TaskSet):
    """
    Warehouse manager: reads warehouse state frequently,
    writes (create/update) much less often.
    """

    @task(10)
    def list_warehouses(self):
        with self.client.get(
            "/api/warehouses/",
            catch_response=True,
            name="WAREHOUSE | GET list",
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                items = data if isinstance(data, list) else data.get("results", [])
                if items:
                    self.user.warehouse_id = items[0].get("id", DEFAULT_WAREHOUSE_ID)
                resp.success()
            else:
                resp.failure(
                    f"WH list → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(8)
    def get_warehouse_detail(self):
        wid = getattr(self.user, "warehouse_id", DEFAULT_WAREHOUSE_ID)
        with self.client.get(
            f"/api/warehouses/{wid}/",
            catch_response=True,
            name="WAREHOUSE | GET detail",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(
                    f"WH detail → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(6)
    def get_warehouse_inventory(self):
        wid = getattr(self.user, "warehouse_id", DEFAULT_WAREHOUSE_ID)
        with self.client.get(
            f"/api/warehouses/{wid}/inventory/",
            catch_response=True,
            name="WAREHOUSE | GET inventory",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(
                    f"WH inventory → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(5)
    def get_warehouse_orders(self):
        wid = getattr(self.user, "warehouse_id", DEFAULT_WAREHOUSE_ID)
        with self.client.get(
            f"/api/warehouses/{wid}/orders/",
            catch_response=True,
            name="WAREHOUSE | GET orders",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(
                    f"WH orders → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(4)
    def get_warehouse_notifications(self):
        wid = getattr(self.user, "warehouse_id", DEFAULT_WAREHOUSE_ID)
        with self.client.get(
            f"/api/warehouses/{wid}/notifications/",
            catch_response=True,
            name="WAREHOUSE | GET notifications",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(
                    f"WH notifications → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(3)
    def get_analytics_summary(self):
        wid = getattr(self.user, "warehouse_id", DEFAULT_WAREHOUSE_ID)
        with self.client.get(
            f"/api/warehouses/{wid}/analytics/summary/",
            catch_response=True,
            name="WAREHOUSE | GET analytics summary",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(
                    f"WH analytics summary → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(3)
    def get_deliveries(self):
        wid = getattr(self.user, "warehouse_id", DEFAULT_WAREHOUSE_ID)
        with self.client.get(
            f"/api/warehouses/{wid}/deliveries/",
            catch_response=True,
            name="WAREHOUSE | GET deliveries",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(
                    f"WH deliveries → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(2)
    def get_rider_payouts(self):
        wid = getattr(self.user, "warehouse_id", DEFAULT_WAREHOUSE_ID)
        with self.client.get(
            f"/api/warehouses/{wid}/rider-payouts/",
            catch_response=True,
            name="WAREHOUSE | GET rider payouts",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(
                    f"WH rider payouts → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(2)
    def get_payout_list(self):
        """GET /api/payments/payouts/list/ – warehouse manager sees own payouts."""
        with self.client.get(
            "/api/payments/payouts/list/",
            catch_response=True,
            name="PAYMENTS | GET payouts list",
        ) as resp:
            if resp.status_code in (200, 403):
                resp.success()
            else:
                resp.failure(
                    f"payouts list → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(2)
    def get_analytics(self):
        """GET /api/analytics/ – ReadOnly ViewSet."""
        with self.client.get(
            "/api/analytics/",
            catch_response=True,
            name="ANALYTICS | GET list",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(
                    f"analytics list → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(1)
    def update_warehouse(self):
        """
        PUT /api/warehouses/{pk}/
        Payload from WarehouseSerializer (writable fields): name, address,
        contact_number, latitude, longitude.
        read_only_fields exclude: id, admin, location, created_at, updated_at.
        """
        wid = getattr(self.user, "warehouse_id", DEFAULT_WAREHOUSE_ID)
        payload = {
            "name": f"Load Test Warehouse {random.randint(1, 100)}",
            "address": "123 Load Test Street, Test City",
            "contact_number": f"+91{random.randint(7000000000, 9999999999)}",
            "latitude": round(random.uniform(8.0, 37.0), 6),
            "longitude": round(random.uniform(68.0, 97.0), 6),
        }
        with self.client.put(
            f"/api/warehouses/{wid}/",
            json=payload,
            catch_response=True,
            name="WAREHOUSE | PUT update",
        ) as resp:
            if resp.status_code in (200, 400, 403, 404):
                resp.success()
            else:
                resp.failure(
                    f"WH update → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(1)
    def mark_notifications_read(self):
        wid = getattr(self.user, "warehouse_id", DEFAULT_WAREHOUSE_ID)
        with self.client.post(
            f"/api/warehouses/{wid}/notifications/mark-read/",
            json={"notification_ids": []},
            catch_response=True,
            name="WAREHOUSE | POST mark notifications read",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(
                    f"WH mark notifications read → HTTP {resp.status_code}: {resp.text[:200]}"
                )
