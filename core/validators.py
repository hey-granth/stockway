"""
Input validation utilities for security hardening
"""

from typing import Tuple
from decimal import Decimal, InvalidOperation
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)


class GeoValidator:
    """Validator for geographical coordinates and distances"""

    MIN_LATITUDE = -90.0
    MAX_LATITUDE = 90.0
    MIN_LONGITUDE = -180.0
    MAX_LONGITUDE = 180.0
    MIN_RADIUS_KM = 1.0
    MAX_RADIUS_KM = 50.0

    @classmethod
    def validate_coordinates(
        cls, latitude: float, longitude: float
    ) -> Tuple[bool, str]:
        """
        Validate latitude and longitude values

        Args:
            latitude: Latitude value
            longitude: Longitude value

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            lat = float(latitude)
            lon = float(longitude)

            if not (cls.MIN_LATITUDE <= lat <= cls.MAX_LATITUDE):
                return (
                    False,
                    f"Latitude must be between {cls.MIN_LATITUDE} and {cls.MAX_LATITUDE}",
                )

            if not (cls.MIN_LONGITUDE <= lon <= cls.MAX_LONGITUDE):
                return (
                    False,
                    f"Longitude must be between {cls.MIN_LONGITUDE} and {cls.MAX_LONGITUDE}",
                )

            return True, ""
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid coordinate format: {e}")
            return False, "Invalid coordinate format"

    @classmethod
    def validate_radius(cls, radius_km: float) -> Tuple[bool, str]:
        """
        Validate radius value and clamp to safe limits

        Args:
            radius_km: Radius in kilometers

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            radius = float(radius_km)

            if radius < cls.MIN_RADIUS_KM:
                return False, f"Radius must be at least {cls.MIN_RADIUS_KM} km"

            if radius > cls.MAX_RADIUS_KM:
                return False, f"Radius must not exceed {cls.MAX_RADIUS_KM} km"

            return True, ""
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid radius format: {e}")
            return False, "Invalid radius format"

    @classmethod
    def clamp_radius(cls, radius_km: float) -> float:
        """
        Clamp radius to safe limits

        Args:
            radius_km: Radius in kilometers

        Returns:
            Clamped radius value
        """
        try:
            radius = float(radius_km)
            return max(cls.MIN_RADIUS_KM, min(radius, cls.MAX_RADIUS_KM))
        except (ValueError, TypeError):
            return cls.MIN_RADIUS_KM


class NumericValidator:
    """Validator for numeric inputs"""

    MIN_QUANTITY = 1
    MAX_QUANTITY = 10000
    MIN_PRICE = Decimal("0.01")
    MAX_PRICE = Decimal("999999.99")

    @classmethod
    def validate_quantity(cls, quantity: int) -> Tuple[bool, str]:
        """
        Validate order quantity

        Args:
            quantity: Quantity value

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            qty = int(quantity)

            if qty < cls.MIN_QUANTITY:
                return False, f"Quantity must be at least {cls.MIN_QUANTITY}"

            if qty > cls.MAX_QUANTITY:
                return False, f"Quantity must not exceed {cls.MAX_QUANTITY}"

            return True, ""
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid quantity format: {e}")
            return False, "Invalid quantity format"

    @classmethod
    def validate_price(cls, price) -> Tuple[bool, str]:
        """
        Validate price value

        Args:
            price: Price value

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            price_decimal = Decimal(str(price))

            if price_decimal < cls.MIN_PRICE:
                return False, f"Price must be at least {cls.MIN_PRICE}"

            if price_decimal > cls.MAX_PRICE:
                return False, f"Price must not exceed {cls.MAX_PRICE}"

            return True, ""
        except (InvalidOperation, ValueError, TypeError) as e:
            logger.warning(f"Invalid price format: {e}")
            return False, "Invalid price format"

    @classmethod
    def validate_positive_integer(
        cls, value: int, field_name: str = "value"
    ) -> Tuple[bool, str]:
        """
        Validate positive integer

        Args:
            value: Integer value
            field_name: Name of field for error message

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            val = int(value)

            if val <= 0:
                return False, f"{field_name} must be a positive integer"

            return True, ""
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid {field_name} format: {e}")
            return False, f"Invalid {field_name} format"


class IDValidator:
    """Validator for database IDs to prevent injection and invalid requests"""

    @classmethod
    def validate_id(cls, id_value, allow_none: bool = False) -> Tuple[bool, str]:
        """
        Validate database ID

        Args:
            id_value: ID value to validate
            allow_none: Whether None is acceptable

        Returns:
            Tuple of (is_valid, error_message)
        """
        if id_value is None:
            if allow_none:
                return True, ""
            return False, "ID is required"

        try:
            id_int = int(id_value)

            if id_int <= 0:
                return False, "ID must be a positive integer"

            if id_int > 2147483647:  # Max PostgreSQL integer
                return False, "ID value too large"

            return True, ""
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid ID format: {e}")
            return False, "Invalid ID format"

    @classmethod
    def validate_id_list(cls, id_list: list) -> Tuple[bool, str]:
        """
        Validate list of IDs

        Args:
            id_list: List of ID values

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(id_list, list):
            return False, "ID list must be an array"

        if len(id_list) == 0:
            return False, "ID list cannot be empty"

        if len(id_list) > 100:
            return False, "Too many IDs in list (max 100)"

        for id_value in id_list:
            is_valid, error_msg = cls.validate_id(id_value)
            if not is_valid:
                return False, error_msg

        return True, ""


class StringValidator:
    """Validator for string inputs"""

    @classmethod
    def validate_length(
        cls, value: str, min_length: int, max_length: int, field_name: str = "field"
    ) -> Tuple[bool, str]:
        """
        Validate string length

        Args:
            value: String value
            min_length: Minimum length
            max_length: Maximum length
            field_name: Name of field for error message

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(value, str):
            return False, f"{field_name} must be a string"

        length = len(value.strip())

        if length < min_length:
            return False, f"{field_name} must be at least {min_length} characters"

        if length > max_length:
            return False, f"{field_name} must not exceed {max_length} characters"

        return True, ""

    @classmethod
    def sanitize_string(cls, value: str) -> str:
        """
        Sanitize string input by removing potentially dangerous characters

        Args:
            value: String to sanitize

        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return str(value)

        # Remove null bytes and control characters (except newline and tab)
        sanitized = "".join(char for char in value if ord(char) >= 32 or char in "\n\t")

        return sanitized.strip()
