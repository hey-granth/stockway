"""
Custom throttling classes for API rate limiting
"""
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class StandardUserThrottle(UserRateThrottle):
    """
    Standard throttle for authenticated users
    Rate configured in settings: 1000/day
    """
    rate = '1000/day'


class StandardAnonThrottle(AnonRateThrottle):
    """
    Standard throttle for anonymous users
    Rate configured in settings: 100/day
    """
    rate = '100/day'


class LocationUpdateThrottle(UserRateThrottle):
    """
    Throttle for rider location updates to prevent spam
    Rate: 60 requests per minute (1 per second)
    """
    rate = '60/min'


class OrderCreationThrottle(UserRateThrottle):
    """
    Throttle for order creation to prevent abuse
    Rate: 30 requests per minute
    """
    rate = '30/min'


class AuthenticationThrottle(UserRateThrottle):
    """
    Throttle for authentication endpoints
    Rate: 10 requests per minute
    """
    rate = '10/min'

