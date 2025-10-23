"""
Geospatial service utilities for warehouse proximity queries using PostGIS.

This module provides functions to find nearby warehouses based on GPS coordinates.
"""

from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.db.models import QuerySet
from warehouses.models import Warehouse


def get_nearby_warehouses(
    latitude, longitude, radius_km=10, limit=None
) -> QuerySet[Warehouse, Warehouse]:
    """
    Find warehouses within a specified radius of a given location.

    Args:
        latitude (float): Latitude of the customer/user location
        longitude (float): Longitude of the customer/user location
        radius_km (float): Search radius in kilometers (default: 10km)
        limit (int): Maximum number of results to return (optional)

    Returns:
        QuerySet: Warehouses ordered by distance with annotated distance field

    Example:
        >>> warehouses = get_nearby_warehouses(28.7041, 77.1025, radius_km=5)
        >>> for warehouse in warehouses:
        >>>     print(f"{warehouse.name}: {warehouse.distance.km:.2f} km away")
    """
    user_location = Point(longitude, latitude, srid=4326)

    queryset = (
        Warehouse.objects.annotate(distance=Distance("location", user_location))
        .filter(distance__lte=D(km=radius_km))
        .order_by("distance")
    )

    if limit:
        queryset = queryset[:limit]

    return queryset


def get_nearest_warehouse(latitude, longitude) -> Warehouse:
    """
    Find the single nearest warehouse to a given location.

    Args:
        latitude (float): Latitude of the customer/user location
        longitude (float): Longitude of the customer/user location

    Returns:
        Warehouse: The nearest warehouse with annotated distance, or None if no warehouses exist

    Example:
        >>> warehouse = get_nearest_warehouse(28.7041, 77.1025)
        >>> if warehouse:
        >>>     print(f"Nearest: {warehouse.name} at {warehouse.distance.km:.2f} km")
    """
    user_location = Point(longitude, latitude, srid=4326)

    return (
        Warehouse.objects.annotate(distance=Distance("location", user_location))
        .order_by("distance")
        .first()
    )


def get_warehouses_with_distance(latitude, longitude) -> QuerySet[Warehouse]:
    """
    Get all warehouses with their distances from a given location.

    Args:
        latitude (float): Latitude of the customer/user location
        longitude (float): Longitude of the customer/user location

    Returns:
        QuerySet: All warehouses ordered by distance with annotated distance field

    Example:
        >>> warehouses = get_warehouses_with_distance(28.7041, 77.1025)
        >>> for warehouse in warehouses[:5]:  # Top 5
        >>>     print(f"{warehouse.name}: {warehouse.distance.km:.2f} km")
    """
    user_location = Point(longitude, latitude, srid=4326)

    return Warehouse.objects.annotate(
        distance=Distance("location", user_location)
    ).order_by("distance")


def validate_coordinates(latitude, longitude) -> tuple[bool, str | None]:
    """
    Validate latitude and longitude values.

    Args:
        latitude (float): Latitude value
        longitude (float): Longitude value

    Returns:
        tuple: (is_valid, error_message)

    Example:
        >>> valid, error = validate_coordinates(28.7041, 77.1025)
        >>> if not valid:
        >>>     print(error)
    """
    try:
        lat = float(latitude)
        lon = float(longitude)

        if lat < -90 or lat > 90:
            return False, "Latitude must be between -90 and 90"

        if lon < -180 or lon > 180:
            return False, "Longitude must be between -180 and 180"

        return True, None
    except (ValueError, TypeError):
        return False, "Invalid coordinate format. Must be numeric values."


def calculate_distance_between_points(lat1, lon1, lat2, lon2) -> Distance:
    """
    Calculate distance between two geographic points.

    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates

    Returns:
        Distance: Django Distance object with km, m, mi attributes

    Example:
        >>> distance = calculate_distance_between_points(28.7041, 77.1025, 28.5355, 77.3910)
        >>> print(f"Distance: {distance.km:.2f} km")
    """
    point1 = Point(lon1, lat1, srid=4326)
    point2 = Point(lon2, lat2, srid=4326)

    from django.contrib.gis.geos import LineString

    line = LineString(point1, point2)
    return Distance(m=line.length)
