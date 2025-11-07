from django.contrib.gis.db.models.functions import Distance
from django.core.cache import cache
from django.db.models import Q
from riders.models import RiderProfile
from core.validators import GeoValidator
import hashlib
import logging

logger = logging.getLogger(__name__)


def find_nearest_available_rider(warehouse, max_distance_km=50):
    """
    Find the nearest available rider to a warehouse using PostGIS with caching.

    Args:
        warehouse: Warehouse instance
        max_distance_km: Maximum distance in kilometers to search for riders

    Returns:
        RiderProfile instance or None
    """
    if not warehouse.location:
        return None

    # Validate and clamp radius
    max_distance_km = GeoValidator.clamp_radius(max_distance_km)

    # Convert km to meters for PostGIS distance calculation
    max_distance_m = max_distance_km * 1000

    # Check if RiderProfile has location field
    if not hasattr(RiderProfile, "location") and not hasattr(
        RiderProfile, "current_location"
    ):
        return None

    location_field = (
        "current_location" if hasattr(RiderProfile, "current_location") else "location"
    )

    # Find available riders within max distance, ordered by distance
    try:
        nearest_rider = (
            RiderProfile.objects.filter(**{f"{location_field}__isnull": False})
            .annotate(distance=Distance(location_field, warehouse.location))
            .filter(distance__lte=max_distance_m)
            .order_by("distance")
            .first()
        )

        return nearest_rider
    except Exception as e:
        logger.error(f"Error finding nearest rider: {e}", exc_info=True)
        return None


def calculate_distance_km(point1, point2):
    """
    Calculate distance between two points in kilometers.

    Args:
        point1: Point object (e.g., warehouse.location)
        point2: Point object (e.g., rider.current_location)

    Returns:
        Distance in kilometers as float
    """
    if not point1 or not point2:
        return None

    try:
        # PostGIS distance is in meters for geography type
        distance_m = point1.distance(point2)
        return distance_m / 1000.0
    except Exception as e:
        logger.error(f"Error calculating distance: {e}", exc_info=True)
        return None


def get_riders_within_radius(warehouse, radius_km=10):
    """
    Get all available riders within a specific radius of the warehouse with caching.

    Args:
        warehouse: Warehouse instance
        radius_km: Radius in kilometers

    Returns:
        QuerySet of RiderProfile instances with distance annotation
    """
    if not warehouse.location:
        return RiderProfile.objects.none()

    # Validate and clamp radius
    is_valid, error_msg = GeoValidator.validate_radius(radius_km)
    if not is_valid:
        logger.warning(f"Invalid radius: {error_msg}")
        radius_km = GeoValidator.clamp_radius(radius_km)

    # Check if RiderProfile has location field
    if not hasattr(RiderProfile, "location") and not hasattr(
        RiderProfile, "current_location"
    ):
        return RiderProfile.objects.none()

    location_field = (
        "current_location" if hasattr(RiderProfile, "current_location") else "location"
    )
    radius_m = radius_km * 1000

    try:
        riders = (
            RiderProfile.objects.filter(**{f"{location_field}__isnull": False})
            .annotate(distance=Distance(location_field, warehouse.location))
            .filter(distance__lte=radius_m)
            .order_by("distance")
        )

        return riders
    except Exception as e:
        logger.error(f"Error getting riders within radius: {e}", exc_info=True)
        return RiderProfile.objects.none()


def find_nearby_warehouses_cached(latitude, longitude, radius_km=10):
    """
    Find nearby warehouses with Redis caching (5 minutes).

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        radius_km: Search radius in kilometers

    Returns:
        List of warehouse instances
    """
    from warehouses.models import Warehouse
    from django.contrib.gis.geos import Point

    # Validate coordinates
    is_valid, error_msg = GeoValidator.validate_coordinates(latitude, longitude)
    if not is_valid:
        logger.warning(f"Invalid coordinates: {error_msg}")
        return []

    # Validate and clamp radius
    radius_km = GeoValidator.clamp_radius(radius_km)

    # Create cache key
    cache_key = _generate_geo_cache_key(latitude, longitude, radius_km)

    # Try to get from cache
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        logger.debug(f"Cache hit for geo query: {cache_key}")
        return cached_result

    # Query database
    try:
        point = Point(longitude, latitude, srid=4326)
        radius_m = radius_km * 1000

        warehouses = list(
            Warehouse.objects.filter(
                location__isnull=False, is_active=True, is_approved=True
            )
            .annotate(distance=Distance("location", point))
            .filter(distance__lte=radius_m)
            .order_by("distance")[:20]  # Limit results
        )

        # Cache for 5 minutes
        cache.set(cache_key, warehouses, 300)
        logger.debug(f"Cached geo query result: {cache_key}")

        return warehouses
    except Exception as e:
        logger.error(f"Error finding nearby warehouses: {e}", exc_info=True)
        return []


def _generate_geo_cache_key(latitude, longitude, radius_km):
    """
    Generate cache key for geo query

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        radius_km: Search radius

    Returns:
        Cache key string
    """
    # Round coordinates to 4 decimal places (~11m precision)
    try:
        lat_rounded = round(float(latitude), 4)
        lon_rounded = round(float(longitude), 4)
        radius_rounded = round(float(radius_km), 1)

        key_string = f"geo:warehouses:{lat_rounded}:{lon_rounded}:{radius_rounded}"
        return key_string
    except Exception:
        return RiderProfile.objects.none()
