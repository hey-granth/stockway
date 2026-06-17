"""
load_tests/tasks/rider_tasks.py
---------------------------------
Task sets for the Rider domain.

Rider endpoints (role: RIDER):
  GET   /api/riders/rider/profile/              RiderProfileView
  GET   /api/riders/rider/orders/               RiderOrdersView
  PATCH /api/riders/rider/orders/update/        RiderOrderUpdateView  { order_id, status }
  PATCH /api/riders/rider/location/update/      RiderLocationUpdateView { latitude, longitude }
  GET   /api/riders/rider/earnings/             RiderEarningsView
  GET   /api/riders/rider/history/              RiderHistoryView
  PATCH /api/riders/rider/live-location/        RiderLiveLocationView  { latitude, longitude }
  GET   /api/riders/rider/performance/          RiderPerformanceView
  PATCH /api/riders/rider/availability/update/  RiderAvailabilityUpdateView { availability }
  GET   /api/riders/rider/notifications/        RiderNotificationsView

Warehouse-side rider endpoints (role: WAREHOUSE_MANAGER):
  GET   /api/riders/warehouse/riders/           WarehouseRidersListView
  GET   /api/riders/warehouse/riders/active/    WarehouseActiveRidersView
  GET   /api/riders/warehouse/riders/metrics/   WarehouseRiderMetricsView
  GET   /api/riders/warehouse/riders/{pk}/      RiderDetailView

Payload shapes from serializers:
  RiderLocationUpdateSerializer : { latitude: float, longitude: float }
  RiderAvailabilitySerializer   : { availability: "available" | "off-duty" }
  OrderStatusUpdateSerializer   : { status: "in_transit" | "delivered" }
"""

import random
from locust import TaskSet, task


# ---------------------------------------------------------------------------
# Rider task set
# ---------------------------------------------------------------------------
class RiderTaskSet(TaskSet):
    """
    Simulates a single active rider: periodic location pings (highest weight),
    reading assigned orders, updating delivery status, and checking notifications.
    """

    # Bounding box roughly centred on India for realistic lat/lng
    _LAT_MIN, _LAT_MAX = 8.0, 37.0
    _LNG_MIN, _LNG_MAX = 68.0, 97.0

    def _random_coords(self):
        lat = round(random.uniform(self._LAT_MIN, self._LAT_MAX), 6)
        lng = round(random.uniform(self._LNG_MIN, self._LNG_MAX), 6)
        return lat, lng

    @task(10)
    def update_location(self):
        """
        PATCH /api/riders/rider/location/update/
        Body: RiderLocationUpdateSerializer { latitude, longitude }
        High weight — riders ping every few seconds in production.
        """
        lat, lng = self._random_coords()
        with self.client.patch(
            "/api/riders/rider/location/update/",
            json={"latitude": lat, "longitude": lng},
            catch_response=True,
            name="RIDER | PATCH location update",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code == 404:
                # Rider profile not created yet for this test user
                resp.success()
            else:
                resp.failure(
                    f"rider location update → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(8)
    def live_location_ping(self):
        """
        PATCH /api/riders/rider/live-location/
        Throttled endpoint; sends same lat/lng payload.
        """
        lat, lng = self._random_coords()
        with self.client.patch(
            "/api/riders/rider/live-location/",
            json={"latitude": lat, "longitude": lng},
            catch_response=True,
            name="RIDER | PATCH live-location",
        ) as resp:
            if resp.status_code in (200, 404, 429):
                # 429 = throttle, expected under load
                resp.success()
            else:
                resp.failure(
                    f"live-location → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(6)
    def get_assigned_orders(self):
        with self.client.get(
            "/api/riders/rider/orders/",
            catch_response=True,
            name="RIDER | GET rider orders",
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                items = data if isinstance(data, list) else data.get("results", [])
                if items:
                    self.user.rider_order_id = items[0].get("id")
                resp.success()
            else:
                resp.failure(
                    f"rider orders → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(3)
    def update_order_status(self):
        """
        PATCH /api/riders/rider/orders/update/
        Body: OrderStatusUpdateSerializer { order_id, status }
        Valid statuses for RIDER role: "in_transit", "delivered"
        """
        order_id = getattr(self.user, "rider_order_id", None)
        if not order_id:
            return
        new_status = random.choice(["in_transit", "delivered"])
        with self.client.patch(
            "/api/riders/rider/orders/update/",
            json={"order_id": order_id, "status": new_status},
            catch_response=True,
            name="RIDER | PATCH order status update",
        ) as resp:
            if resp.status_code in (200, 400, 404):
                # 400 → invalid transition (e.g., already delivered)
                resp.success()
            else:
                resp.failure(
                    f"rider order update → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(3)
    def get_profile(self):
        with self.client.get(
            "/api/riders/rider/profile/",
            catch_response=True,
            name="RIDER | GET rider profile",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(
                    f"rider profile → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(2)
    def toggle_availability(self):
        """PATCH /api/riders/rider/availability/update/ { availability: "available"|"off-duty" }"""
        avail = random.choice(["available", "off-duty"])
        with self.client.patch(
            "/api/riders/rider/availability/update/",
            json={"availability": avail},
            catch_response=True,
            name="RIDER | PATCH availability",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(
                    f"rider availability → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(2)
    def get_notifications(self):
        with self.client.get(
            "/api/riders/rider/notifications/",
            catch_response=True,
            name="RIDER | GET rider notifications",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(
                    f"rider notifications → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(1)
    def get_earnings(self):
        with self.client.get(
            "/api/riders/rider/earnings/",
            catch_response=True,
            name="RIDER | GET earnings",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(
                    f"rider earnings → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(1)
    def get_performance(self):
        with self.client.get(
            "/api/riders/rider/performance/",
            catch_response=True,
            name="RIDER | GET performance",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(
                    f"rider performance → HTTP {resp.status_code}: {resp.text[:200]}"
                )


# ---------------------------------------------------------------------------
# Warehouse-side rider management tasks (used in WarehouseManagerUser)
# ---------------------------------------------------------------------------
class WarehouseRiderManagementTasks(TaskSet):
    """
    Warehouse manager viewing and managing riders.
    Mixed into the WarehouseManagerUser alongside WarehouseOrderTasks.
    """

    @task(5)
    def list_warehouse_riders(self):
        with self.client.get(
            "/api/riders/warehouse/riders/",
            catch_response=True,
            name="RIDER-MGMT | WH GET riders list",
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                items = data if isinstance(data, list) else data.get("results", [])
                if items:
                    self.user.sample_rider_id = items[0].get("id")
                resp.success()
            else:
                resp.failure(
                    f"WH riders list → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(3)
    def get_active_riders(self):
        with self.client.get(
            "/api/riders/warehouse/riders/active/",
            catch_response=True,
            name="RIDER-MGMT | WH GET active riders",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(
                    f"WH active riders → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(2)
    def get_rider_metrics(self):
        with self.client.get(
            "/api/riders/warehouse/riders/metrics/",
            catch_response=True,
            name="RIDER-MGMT | WH GET rider metrics",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(
                    f"WH rider metrics → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(2)
    def get_rider_detail(self):
        rider_id = getattr(self.user, "sample_rider_id", None)
        if not rider_id:
            return
        with self.client.get(
            f"/api/riders/warehouse/riders/{rider_id}/",
            catch_response=True,
            name="RIDER-MGMT | WH GET rider detail",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(
                    f"WH rider detail → HTTP {resp.status_code}: {resp.text[:200]}"
                )
