"""
Security middleware for request tracking and security headers
"""

import uuid
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class CorrelationIDMiddleware(MiddlewareMixin):
    """
    Middleware to add correlation ID to each request for tracking and debugging
    """

    def process_request(self, request):
        """Add correlation ID to request"""
        correlation_id = request.META.get("HTTP_X_CORRELATION_ID")

        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        request.correlation_id = correlation_id

    def process_response(self, request, response):
        """Add correlation ID to response headers"""
        if hasattr(request, "correlation_id"):
            response["X-Correlation-ID"] = request.correlation_id

        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers to all responses
    """

    def process_response(self, request, response):
        """Add security headers"""
        # Prevent clickjacking
        response["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response["X-Content-Type-Options"] = "nosniff"

        # Enable XSS protection
        response["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy (adjust as needed)
        response["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:;"
        )

        # Permissions Policy (formerly Feature-Policy)
        response["Permissions-Policy"] = "geolocation=(self), microphone=(), camera=()"

        return response
