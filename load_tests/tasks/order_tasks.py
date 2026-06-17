"""
load_tests/tasks/order_tasks.py
---------------------------------
Task sets for the Orders domain, split by role.

Shopkeeper endpoints (prefix /api/orders/shopkeeper/):
  POST /api/orders/shopkeeper/orders/create/      OrderCreateView     (IsShopkeeper)
  GET  /api/orders/shopkeeper/orders/             ShopkeeperOrderList (IsShopkeeper)
  GET  /api/orders/shopkeeper/orders/{pk}/        ShopkeeperOrderDetail

Warehouse endpoints (prefix /api/orders/warehouse/):
  GET  /api/orders/warehouse/orders/              WarehouseOrderList  (IsWarehouseAdmin)
  GET  /api/orders/warehouse/orders/pending/      WarehousePendingOrders
  GET  /api/orders/warehouse/orders/{pk}/         WarehouseOrderDetail
  POST /api/orders/warehouse/orders/{pk}/accept/  OrderAcceptView
  POST /api/orders/warehouse/orders/{pk}/reject/  OrderRejectView     (body: rejection_reason)
  POST /api/orders/warehouse/orders/assign/       OrderAssignmentView (body: order_id, rider_id)

Payload shapes derived from:
  - OrderCreateSerializer: { warehouse_id: int, items: [{item_id, quantity}], notes? }
  - OrderAssignmentSerializer: { order_id: int, rider_id: int }
  - OrderRejectView: { rejection_reason: str (10–500 chars) }
"""

import random
from locust import TaskSet, task

from load_tests.config import DEFAULT_WAREHOUSE_ID, DEFAULT_ITEM_ID


# ---------------------------------------------------------------------------
# Shopkeeper task set
# ---------------------------------------------------------------------------
class ShopkeeperOrderTasks(TaskSet):
    """
    Realistic shopkeeper traffic: mostly reading own orders,
    occasionally browsing inventory and placing new orders.
    """

    @task(10)
    def list_my_orders(self):
        with self.client.get(
            "/api/orders/shopkeeper/orders/",
            catch_response=True,
            name="ORDERS | SK GET orders list",
        ) as resp:
            if resp.status_code == 200:
                # Cache a real order ID for the detail task
                results = resp.json()
                if isinstance(results, list) and results:
                    self.user.sample_order_id = results[0].get("id", 1)
                elif isinstance(results, dict):
                    items = results.get("results", [])
                    if items:
                        self.user.sample_order_id = items[0].get("id", 1)
                resp.success()
            else:
                resp.failure(
                    f"SK list orders → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(5)
    def get_order_detail(self):
        order_id = getattr(self.user, "sample_order_id", 1)
        with self.client.get(
            f"/api/orders/shopkeeper/orders/{order_id}/",
            catch_response=True,
            name="ORDERS | SK GET order detail",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(
                    f"SK order detail → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(2)
    def create_order(self):
        """
        POST /api/orders/shopkeeper/orders/create/
        Payload: OrderCreateSerializer { warehouse_id, items: [{item_id, quantity}] }
        Note: Will return 400 if stock is insufficient or a pending order
        already exists – both are tracked as successes here since they reflect
        realistic state, not infrastructure failures.
        """
        wid = getattr(self.user, "warehouse_id", DEFAULT_WAREHOUSE_ID)
        item_id = getattr(self.user, "sample_item_id", DEFAULT_ITEM_ID)
        payload = {
            "warehouse_id": wid,
            "items": [
                {"item_id": item_id, "quantity": random.randint(1, 3)}
            ],
            "notes": "Load test order",
        }
        with self.client.post(
            "/api/orders/shopkeeper/orders/create/",
            json=payload,
            catch_response=True,
            name="ORDERS | SK POST create order",
        ) as resp:
            if resp.status_code == 201:
                created_id = resp.json().get("id")
                if created_id:
                    self.user.sample_order_id = created_id
                resp.success()
            elif resp.status_code in (400, 404, 429):
                # Insufficient stock / duplicate pending order / item not found / throttled
                # — business-logic rejection, not a server fault
                resp.success()
            else:
                resp.failure(
                    f"SK create order → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(1)
    def browse_inventory(self):
        """GET /api/shopkeeper/inventory/browse/ — item catalogue for shopkeeper."""
        with self.client.get(
            "/api/shopkeepers/inventory/browse/",
            catch_response=True,
            name="ORDERS | SK GET browse inventory",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(
                    f"SK browse inventory → HTTP {resp.status_code}: {resp.text[:200]}"
                )


# ---------------------------------------------------------------------------
# Warehouse task set
# ---------------------------------------------------------------------------
class WarehouseOrderTasks(TaskSet):
    """
    Warehouse manager traffic: reads, accepts pending orders, occasional
    rider assignment and rejection.
    """

    @task(10)
    def list_warehouse_orders(self):
        with self.client.get(
            "/api/orders/warehouse/orders/",
            catch_response=True,
            name="ORDERS | WH GET orders list",
        ) as resp:
            if resp.status_code == 200:
                results = resp.json()
                items = (
                    results if isinstance(results, list)
                    else results.get("results", [])
                )
                if items:
                    self.user.sample_order_id = items[0].get("id", 1)
                resp.success()
            else:
                resp.failure(
                    f"WH list orders → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(7)
    def list_pending_orders(self):
        with self.client.get(
            "/api/orders/warehouse/orders/pending/",
            catch_response=True,
            name="ORDERS | WH GET pending orders",
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                items = data if isinstance(data, list) else data.get("results", [])
                if items:
                    self.user.pending_order_id = items[0].get("id")
                resp.success()
            else:
                resp.failure(
                    f"WH pending orders → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(4)
    def get_order_detail(self):
        order_id = getattr(self.user, "sample_order_id", 1)
        with self.client.get(
            f"/api/orders/warehouse/orders/{order_id}/",
            catch_response=True,
            name="ORDERS | WH GET order detail",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(
                    f"WH order detail → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(3)
    def accept_order(self):
        """POST /api/orders/warehouse/orders/{pk}/accept/  – no body required."""
        order_id = getattr(self.user, "pending_order_id", None)
        if not order_id:
            return  # Nothing to accept yet
        with self.client.post(
            f"/api/orders/warehouse/orders/{order_id}/accept/",
            json={},
            catch_response=True,
            name="ORDERS | WH POST accept order",
        ) as resp:
            if resp.status_code in (200, 400, 404):
                # 400 → already accepted/rejected; 404 → race-condition with other workers
                resp.success()
            else:
                resp.failure(
                    f"WH accept order → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(1)
    def reject_order(self):
        """
        POST /api/orders/warehouse/orders/{pk}/reject/
        Body: { rejection_reason: str (10-500 chars) }
        """
        order_id = getattr(self.user, "pending_order_id", None)
        if not order_id:
            return
        with self.client.post(
            f"/api/orders/warehouse/orders/{order_id}/reject/",
            json={"rejection_reason": "Load test – automated rejection for testing purposes"},
            catch_response=True,
            name="ORDERS | WH POST reject order",
        ) as resp:
            if resp.status_code in (200, 400, 404):
                resp.success()
            else:
                resp.failure(
                    f"WH reject order → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(1)
    def assign_rider(self):
        """
        POST /api/orders/warehouse/orders/assign/
        Body: OrderAssignmentSerializer { order_id: int, rider_id: int }
        """
        order_id = getattr(self.user, "sample_order_id", None)
        rider_id = getattr(self.user, "sample_rider_id", None)
        if not order_id or not rider_id:
            return
        with self.client.post(
            "/api/orders/warehouse/orders/assign/",
            json={"order_id": order_id, "rider_id": rider_id},
            catch_response=True,
            name="ORDERS | WH POST assign rider",
        ) as resp:
            if resp.status_code in (200, 201, 400, 404):
                resp.success()
            else:
                resp.failure(
                    f"WH assign rider → HTTP {resp.status_code}: {resp.text[:200]}"
                )
