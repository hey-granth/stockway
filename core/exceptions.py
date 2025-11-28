"""
Custom exceptions for the application.
Provides structured error handling across all domain apps.
"""

from rest_framework.exceptions import APIException, ValidationError
from rest_framework import status
from rest_framework.response import Response
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404
import logging

logger = logging.getLogger(__name__)


class BusinessLogicError(APIException):
    """Base exception for business logic errors."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A business logic error occurred."
    default_code = "business_logic_error"


class InsufficientStockError(BusinessLogicError):
    """Raised when inventory stock is insufficient for an order."""

    default_detail = "Insufficient stock available."
    default_code = "insufficient_stock"


class InvalidOrderStateError(BusinessLogicError):
    """Raised when attempting invalid state transitions on orders."""

    default_detail = "Invalid order state transition."
    default_code = "invalid_order_state"


class InvalidStateTransitionError(BusinessLogicError):
    """Raised when an invalid order state transition is attempted."""

    default_detail = "Invalid state transition."
    default_code = "invalid_state_transition"


class PaymentError(BusinessLogicError):
    """Raised when payment processing fails."""

    default_detail = "Payment processing failed."
    default_code = "payment_error"


class UnauthorizedActionError(APIException):
    """Raised when user attempts unauthorized action."""

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You are not authorized to perform this action."
    default_code = "unauthorized_action"


class UnauthorizedAccessError(APIException):
    """Raised when user attempts to access resources they don't own."""

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have permission to access this resource."
    default_code = "unauthorized_access"


class ResourceNotFoundError(APIException):
    """Raised when a requested resource is not found."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "The requested resource was not found."
    default_code = "resource_not_found"


class ProfileNotCompleteError(BusinessLogicError):
    """Raised when user profile is incomplete for an operation."""

    default_detail = "Please complete your profile before proceeding."
    default_code = "profile_incomplete"


def custom_exception_handler(exc, context):
    """
    Custom exception handler that standardizes error responses
    and hides stack traces in production

    Args:
        exc: Exception instance
        context: Context dict with view and request

    Returns:
        Response object with standardized error format
    """
    # Import here to avoid circular dependency
    from rest_framework.views import exception_handler

    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # Log the exception
    request = context.get("request")
    view = context.get("view")

    log_data = {
        "exception_type": type(exc).__name__,
        "path": request.path if request else None,
        "method": request.method if request else None,
        "user_id": request.user.id
        if request and hasattr(request, "user") and request.user.is_authenticated
        else None,
    }

    # If response is None, it's not a DRF exception
    if response is None:
        # Handle Django core exceptions
        if isinstance(exc, Http404):
            response = Response(
                {
                    "error": "Resource not found",
                    "detail": "The requested resource does not exist",
                },
                status=404,
            )
        elif isinstance(exc, PermissionDenied):
            response = Response(
                {
                    "error": "Permission denied",
                    "detail": "You do not have permission to perform this action",
                },
                status=403,
            )
        else:
            # Log unexpected errors
            logger.error(
                f"Unhandled exception: {str(exc)}", exc_info=True, extra=log_data
            )

            # Return generic error in production, detailed in development
            if settings.DEBUG:
                response = Response(
                    {
                        "error": "Internal server error",
                        "detail": str(exc),
                        "type": type(exc).__name__,
                    },
                    status=500,
                )
            else:
                response = Response(
                    {
                        "error": "Internal server error",
                        "detail": "An unexpected error occurred. Please try again later.",
                    },
                    status=500,
                )
    else:
        # Standardize DRF exception responses
        if hasattr(response, "data"):
            # Log auth failures and permission denials
            if response.status_code in [401, 403]:
                logger.warning(f"Access denied: {response.status_code}", extra=log_data)

            # Convert 403 to 401 for unauthenticated users
            # This ensures consistency: unauthenticated = 401, unauthorized = 403
            if (
                response.status_code == 403
                and request
                and (
                    not hasattr(request, "user")
                    or not request.user
                    or not request.user.is_authenticated
                )
            ):
                response.status_code = 401
                if isinstance(response.data, dict) and "detail" in response.data:
                    response.data["detail"] = (
                        "Authentication credentials were not provided."
                    )

            # Standardize error format
            if isinstance(response.data, dict):
                # Check if already in standard format
                if "error" not in response.data:
                    error_data = {"error": "Request failed"}

                    # Handle validation errors
                    if isinstance(exc, ValidationError):
                        error_data["error"] = "Validation failed"
                        error_data["detail"] = response.data
                    else:
                        # Use detail if available
                        if "detail" in response.data:
                            error_data["detail"] = response.data["detail"]
                        else:
                            error_data["detail"] = response.data

                    response.data = error_data
            else:
                # Wrap non-dict responses
                response.data = {"error": "Request failed", "detail": response.data}

    # Add correlation ID for tracing
    if request and hasattr(request, "correlation_id"):
        response["X-Correlation-ID"] = request.correlation_id

    return response
