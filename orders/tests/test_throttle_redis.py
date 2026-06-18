import os
import time
from unittest.mock import patch
import redis

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import User

TEST_REDIS_URL = os.environ.get("TEST_REDIS_URL", "redis://localhost:6379/2")

TEST_CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": TEST_REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}


@override_settings(
    CACHES=TEST_CACHES,
    DEFAULT_THROTTLE_CLASSES=["core.throttling.OrderCreationThrottle"],
)
class RedisThrottleIntegrationTests(TestCase):
    def setUp(self):
        # Flush the test Redis DB
        self.redis_client = redis.from_url(TEST_REDIS_URL)
        self.redis_client.flushdb()

        self.shopkeeper = User.objects.create_user(
            email="throttle_test@example.com", role="SHOPKEEPER"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.shopkeeper)
        self.url = "/api/shopkeeper/orders/create/"

    def tearDown(self):
        self.redis_client.flushdb()

    @patch("core.throttling.OrderCreationThrottle.rate", "3/min")
    def test_redis_throttle(self):
        """
        Test that Redis throttling works correctly:
        1. Single user can make requests up to throttle limit
        2. Next request returns 429
        3. After throttle window expires, requests are accepted
        """
        # The throttle limits to 3 per minute.
        # Send 3 requests, all should not be 429. (They will be 400 Bad Request, which is fine)
        for _ in range(3):
            response = self.client.post(self.url, {}, format="json")
            self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # 4th request should be throttled
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # Mock time to advance 61 seconds
        future_time = time.time() + 61
        with patch(
            "rest_framework.throttling.SimpleRateThrottle.timer",
            return_value=future_time,
        ):
            # Now the request should be allowed again
            response = self.client.post(self.url, {}, format="json")
            self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
