"""
load_tests/tasks/shopkeeper_tasks.py
--------------------------------------
Task sets specific to the Shopkeeper role that are not covered in
order_tasks.py or rider_tasks.py.

Shopkeeper-specific endpoints (prefix /api/shopkeepers/):
  GET  /api/shopkeepers/orders/                        ShopkeeperOrderListView
  GET  /api/shopkeepers/orders/{pk}/                   ShopkeeperOrderDetailView
  GET  /api/shopkeepers/orders/{pk}/tracking/          ShopkeeperOrderTrackingView
  GET  /api/shopkeepers/payments/                      ShopkeeperPaymentListView
  GET  /api/shopkeepers/payments/summary/              ShopkeeperPaymentSummaryView
  GET  /api/shopkeepers/inventory/browse/              ShopkeeperInventoryBrowseView
  GET  /api/shopkeepers/warehouses/nearby/             ShopkeeperNearbyWarehousesView
  GET  /api/shopkeepers/notifications/                 ShopkeeperNotificationListView
  POST /api/shopkeepers/notifications/mark-read/       ShopkeeperNotificationMarkReadView
  GET  /api/shopkeepers/notifications/unread-count/    ShopkeeperNotificationUnreadCountView
  POST /api/shopkeepers/support/tickets/create/        ShopkeeperSupportTicketCreateView
  GET  /api/shopkeepers/support/tickets/               ShopkeeperSupportTicketListView
  GET  /api/shopkeepers/analytics/                     ShopkeeperAnalyticsView

Also covers generic notification endpoint available to all roles:
  GET  /api/notifications/                            NotificationListView
  PATCH /api/notifications/read/                      MarkNotificationReadView
"""

import random
from locust import TaskSet, task


class ShopkeeperBrowseTasks(TaskSet):
    """
    High-frequency read tasks: browsing inventory, checking warehouse list,
    reading notifications. These dominate shopkeeper traffic.
    """

    @task(12)
    def browse_inventory(self):
        with self.client.get(
            "/api/shopkeepers/inventory/browse/",
            catch_response=True,
            name="SK | GET browse inventory",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(
                    f"SK browse inventory → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(8)
    def list_my_orders(self):
        with self.client.get(
            "/api/shopkeepers/orders/",
            catch_response=True,
            name="SK | GET shopkeeper orders",
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                items = data if isinstance(data, list) else data.get("results", [])
                if items:
                    self.user.sample_order_id = items[0].get("id")
                resp.success()
            else:
                resp.failure(
                    f"SK orders list → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(5)
    def get_order_detail(self):
        order_id = getattr(self.user, "sample_order_id", None)
        if not order_id:
            return
        with self.client.get(
            f"/api/shopkeepers/orders/{order_id}/",
            catch_response=True,
            name="SK | GET order detail",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(
                    f"SK order detail → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(4)
    def track_order(self):
        order_id = getattr(self.user, "sample_order_id", None)
        if not order_id:
            return
        with self.client.get(
            f"/api/shopkeepers/orders/{order_id}/tracking/",
            catch_response=True,
            name="SK | GET order tracking",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(
                    f"SK order tracking → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(4)
    def get_notifications(self):
        with self.client.get(
            "/api/shopkeepers/notifications/",
            catch_response=True,
            name="SK | GET notifications",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(
                    f"SK notifications → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(3)
    def get_unread_count(self):
        with self.client.get(
            "/api/shopkeepers/notifications/unread-count/",
            catch_response=True,
            name="SK | GET notification unread count",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(
                    f"SK unread count → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(3)
    def get_nearby_warehouses(self):
        with self.client.get(
            "/api/shopkeepers/warehouses/nearby/?latitude=28.6139&longitude=77.2090",
            catch_response=True,
            name="SK | GET nearby warehouses",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(
                    f"SK nearby warehouses → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(2)
    def get_payments(self):
        with self.client.get(
            "/api/shopkeepers/payments/",
            catch_response=True,
            name="SK | GET payments",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(
                    f"SK payments → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(2)
    def get_payment_summary(self):
        with self.client.get(
            "/api/shopkeepers/payments/summary/",
            catch_response=True,
            name="SK | GET payment summary",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(
                    f"SK payment summary → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(2)
    def get_analytics(self):
        with self.client.get(
            "/api/shopkeepers/analytics/",
            catch_response=True,
            name="SK | GET shopkeeper analytics",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(
                    f"SK analytics → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(1)
    def mark_notifications_read(self):
        """
        POST /api/shopkeepers/notifications/mark-read/
        Body shape from NotificationMarkReadSerializer – mark all via flag.
        """
        with self.client.post(
            "/api/shopkeepers/notifications/mark-read/",
            json={"mark_all": True},
            catch_response=True,
            name="SK | POST mark notifications read",
        ) as resp:
            if resp.status_code in (200, 204):
                resp.success()
            else:
                resp.failure(
                    f"SK mark read → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(1)
    def list_support_tickets(self):
        with self.client.get(
            "/api/shopkeepers/support/tickets/",
            catch_response=True,
            name="SK | GET support tickets",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(
                    f"SK support tickets → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(1)
    def create_support_ticket(self):
        """
        POST /api/shopkeepers/support/tickets/create/
        Body from SupportTicketCreateSerializer: { category, subject, description, order? }
        The 'order' field is optional (FK to Order).
        """
        CATEGORIES = ["general", "payment", "delivery", "order", "other"]
        payload = {
            "category": random.choice(CATEGORIES),
            "subject": "Load test support ticket subject",
            "description": (
                "This ticket was created by an automated Locust load test. "
                "Please disregard. Issue: simulated problem during test run."
            ),
        }
        order_id = getattr(self.user, "sample_order_id", None)
        if order_id:
            payload["order"] = order_id
        with self.client.post(
            "/api/shopkeepers/support/tickets/create/",
            json=payload,
            catch_response=True,
            name="SK | POST create support ticket",
        ) as resp:
            if resp.status_code in (201, 400, 404):
                # 400/404 → invalid category or order FK – acceptable
                resp.success()
            else:
                resp.failure(
                    f"SK create ticket → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(1)
    def generic_notification_list(self):
        """GET /api/notifications/ — cross-role notification feed."""
        with self.client.get(
            "/api/notifications/",
            catch_response=True,
            name="NOTIF | GET notifications (generic)",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(
                    f"generic notifications → HTTP {resp.status_code}: {resp.text[:200]}"
                )
