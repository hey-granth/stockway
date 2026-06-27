"""
Custom throttling classes for API rate limiting
"""

from django.conf import settings
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class LoadTestThrottleMixin:
    def allow_request(self, request, view):
        if getattr(settings, "LOAD_TEST", False):
            return True
        return super().allow_request(request, view)


class StandardUserThrottle(LoadTestThrottleMixin, UserRateThrottle):
    """
    Standard throttle for authenticated users
    Rate configured in settings: 1000/day
    """

    rate = "1000/day"


class StandardAnonThrottle(LoadTestThrottleMixin, AnonRateThrottle):
    """
    Standard throttle for anonymous users
    Rate configured in settings: 100/day
    """

    rate = "100/day"


class LocationUpdateThrottle(LoadTestThrottleMixin, UserRateThrottle):
    """
    Throttle for rider location updates to prevent spam
    Rate: 60 requests per minute (1 per second)
    """

    rate = "60/min"


class OrderCreationThrottle(LoadTestThrottleMixin, UserRateThrottle):
    """
    Throttle for order creation to prevent abuse
    Rate: 30 requests per minute
    """

    rate = "30/min"


class AuthenticationThrottle(LoadTestThrottleMixin, UserRateThrottle):
    """
    Throttle for authentication endpoints
    Rate: 10 requests per minute
    """

    rate = "10/min"
