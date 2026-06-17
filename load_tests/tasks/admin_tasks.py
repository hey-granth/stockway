"""
load_tests/tasks/admin_tasks.py
---------------------------------
Task set for the Admin / SuperAdmin role.

Endpoints accessible only to ADMIN (is_superuser=True or role=="ADMIN"):
  GET  /api/accounts/admin/users/                   AdminUserListView     (IsSuperAdmin)
  GET  /api/accounts/admin/users/{id}/              AdminUserDetailView
  GET  /api/accounts/admin/users/{id}/dependencies/ AdminUserDependenciesView
  GET  /api/analytics/system/                       AnalyticsViewSet custom action
  GET  /api/analytics/warehouse/                    AnalyticsViewSet (IsSuperAdmin | IsWarehouseAdmin)
  GET  /api/riders/admin/riders/manage/             AdminRiderManagementView
  GET  /api/riders/admin/riders/export/payouts/     AdminRiderPayoutExportView
  GET  /api/payments/payouts/list/                  list_payouts (ADMIN sees all)

NOTE: Destructive admin operations (deactivate, hard-delete) are excluded
from load tests intentionally – those cannot safely be run repeatedly against
a shared test database without pre-seeded throwaway users.
"""

from locust import TaskSet, task


class AdminTaskSet(TaskSet):
    """Admin traffic is very low volume but covers privileged read paths."""

    @task(10)
    def list_users(self):
        with self.client.get(
            "/api/accounts/admin/users/",
            catch_response=True,
            name="ADMIN | GET users list",
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                items = data if isinstance(data, list) else data.get("results", [])
                if items:
                    self.user.sample_user_id = items[0].get("id")
                resp.success()
            else:
                resp.failure(
                    f"admin users list → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(5)
    def get_user_detail(self):
        uid = getattr(self.user, "sample_user_id", None)
        if not uid:
            return
        with self.client.get(
            f"/api/accounts/admin/users/{uid}/",
            catch_response=True,
            name="ADMIN | GET user detail",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(
                    f"admin user detail → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(3)
    def get_user_dependencies(self):
        uid = getattr(self.user, "sample_user_id", None)
        if not uid:
            return
        with self.client.get(
            f"/api/accounts/admin/users/{uid}/dependencies/",
            catch_response=True,
            name="ADMIN | GET user dependencies",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(
                    f"admin user deps → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(3)
    def get_rider_management(self):
        with self.client.get(
            "/api/riders/warehouse/riders/",
            catch_response=True,
            name="ADMIN | GET rider management",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(
                    f"admin rider manage → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(2)
    def get_payout_export(self):
        with self.client.get(
            "/api/riders/admin/riders/export/payouts/",
            catch_response=True,
            name="ADMIN | GET rider payout export",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(
                    f"admin payout export → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(2)
    def list_all_payouts(self):
        with self.client.get(
            "/api/payments/payouts/list/",
            catch_response=True,
            name="ADMIN | GET all payouts",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(
                    f"admin payouts list → HTTP {resp.status_code}: {resp.text[:200]}"
                )

    @task(1)
    def get_analytics(self):
        with self.client.get(
            "/api/analytics/",
            catch_response=True,
            name="ADMIN | GET analytics list",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(
                    f"admin analytics → HTTP {resp.status_code}: {resp.text[:200]}"
                )
