"""
load_tests/tasks/auth_tasks.py
-------------------------------
Shared on_start auth helper and a lightweight CurrentUser task
that every user role calls periodically to simulate session validation.

The auth flow matches the actual codebase:
  POST /api/accounts/signin/  { email, password }
  → { access_token, token_type, ... }
  Authorization: Bearer <access_token>
"""

from locust import TaskSet, task


def do_login(user_client, email: str, password: str) -> str | None:
    """
    Perform the signin flow and inject the Bearer token into the
    client's default headers.

    Returns the access_token string on success, None on failure
    (the failure is already recorded via catch_response).
    """
    with user_client.post(
        "/api/accounts/signin/",
        json={"email": email, "password": password},
        catch_response=True,
        name="AUTH | signin",
    ) as resp:
        if resp.status_code == 200:
            data = resp.json()
            token = data.get("access_token")
            if not token:
                resp.failure("signin 200 but no access_token in response body")
                return None
            # Inject into every subsequent request
            user_client.headers.update({"Authorization": f"Bearer {token}"})
            resp.success()
            return token
        else:
            resp.failure(
                f"signin failed: HTTP {resp.status_code} – {resp.text[:200]}"
            )
            return None


class CurrentUserTasks(TaskSet):
    """Periodic GET /api/accounts/me/ – valid for ALL roles."""

    @task
    def get_me(self):
        with self.client.get(
            "/api/accounts/me/",
            catch_response=True,
            name="AUTH | GET /me/",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"GET /me/ → HTTP {resp.status_code}")
