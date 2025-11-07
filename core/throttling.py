"""
Rate limiting and throttling for API endpoints
"""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class AuthThrottle(AnonRateThrottle):
    """
    Throttle for authentication endpoints (login, signup, OTP)
    """

    rate = "10/hour"  # 10 requests per hour per IP


class OTPThrottle(AnonRateThrottle):
    """
    Strict throttle for OTP generation endpoints
    """

    rate = "5/hour"  # 5 OTP requests per hour per IP


class GeoQueryThrottle(UserRateThrottle):
    """
    Throttle for geo query endpoints (nearby warehouses, rider search)
    """

    rate = "60/minute"  # 60 requests per minute per user


class OrderCreationThrottle(UserRateThrottle):
    """
    Throttle for order creation
    """

    rate = "20/hour"  # 20 orders per hour per user


class StandardUserThrottle(UserRateThrottle):
    """
    Standard throttle for authenticated users
    """

    rate = "1000/day"  # 1000 requests per day per user


class StandardAnonThrottle(AnonRateThrottle):
    """
    Standard throttle for anonymous users
    """

    rate = "100/day"  # 100 requests per day per IP
