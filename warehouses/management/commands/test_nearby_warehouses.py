"""
Management command to verify PostGIS spatial index and test nearby warehouse detection.
"""

from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance as DistanceFunc
from django.contrib.gis.measure import Distance
from django.db import connection
from warehouses.models import Warehouse
from accounts.models import User


class Command(BaseCommand):
    help = "Verify PostGIS spatial index and test nearby warehouse detection"

    def add_arguments(self, parser):
        parser.add_argument(
            "--latitude",
            type=float,
            default=28.6139,
            help="Latitude for test query (default: 28.6139 - New Delhi)",
        )
        parser.add_argument(
            "--longitude",
            type=float,
            default=77.2090,
            help="Longitude for test query (default: 77.2090 - New Delhi)",
        )
        parser.add_argument(
            "--radius",
            type=float,
            default=10,
            help="Search radius in kilometers (default: 10)",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS("WAREHOUSE SPATIAL INDEX VERIFICATION"))
        self.stdout.write(self.style.SUCCESS("=" * 60 + "\n"))

        # 1. Check PostGIS extension
        self.check_postgis()

        # 2. Check spatial index on location field
        self.check_spatial_index()

        # 3. Test nearby warehouse query
        lat = options["latitude"]
        lon = options["longitude"]
        radius = options["radius"]
        self.test_nearby_query(lat, lon, radius)

        # 4. Performance benchmark
        self.benchmark_query(lat, lon, radius)

        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS("VERIFICATION COMPLETE"))
        self.stdout.write(self.style.SUCCESS("=" * 60 + "\n"))

    def check_postgis(self):
        """Check if PostGIS extension is installed"""
        self.stdout.write(self.style.WARNING("Checking PostGIS extension..."))

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT extname, extversion 
                FROM pg_extension 
                WHERE extname = 'postgis'
            """)
            result = cursor.fetchone()

            if result:
                self.stdout.write(
                    self.style.SUCCESS(f"✓ PostGIS is installed (version: {result[1]})")
                )
            else:
                self.stdout.write(self.style.ERROR("✗ PostGIS is not installed!"))

    def check_spatial_index(self):
        """Check if spatial index exists on location field"""
        self.stdout.write(self.style.WARNING("\nChecking spatial index..."))

        with connection.cursor() as cursor:
            # Get table name
            table_name = Warehouse._meta.db_table

            # Check for GIST index on location field
            cursor.execute(
                """
                SELECT 
                    indexname, 
                    indexdef
                FROM pg_indexes
                WHERE tablename = %s
                AND indexdef LIKE '%%location%%'
                AND indexdef LIKE '%%gist%%'
            """,
                [table_name],
            )

            results = cursor.fetchall()

            if results:
                for result in results:
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Spatial index found: {result[0]}")
                    )
                    self.stdout.write(f"  Index definition: {result[1][:80]}...")
            else:
                self.stdout.write(
                    self.style.ERROR("✗ No spatial index found on location field!")
                )
                self.stdout.write(
                    self.style.WARNING(
                        "  Note: Django should create this automatically."
                    )
                )

    def test_nearby_query(self, lat, lon, radius):
        """Test nearby warehouse query"""
        self.stdout.write(self.style.WARNING(f"\nTesting nearby warehouse query..."))
        self.stdout.write(f"  Location: ({lat}, {lon})")
        self.stdout.write(f"  Radius: {radius} km")

        # Create point
        user_location = Point(lon, lat, srid=4326)

        # Query warehouses
        nearby_warehouses = (
            Warehouse.objects.filter(
                location__isnull=False,
                is_active=True,
                is_approved=True,
                location__distance_lte=(user_location, Distance(km=radius)),
            )
            .annotate(distance=DistanceFunc("location", user_location))
            .order_by("distance")
        )

        count = nearby_warehouses.count()
        self.stdout.write(f"\n  Found {count} warehouse(s) within {radius} km")

        if count > 0:
            nearest = nearby_warehouses.first()
            self.stdout.write(self.style.SUCCESS(f"\n  ✓ Nearest warehouse:"))
            self.stdout.write(f"    ID: {nearest.id}")
            self.stdout.write(f"    Name: {nearest.name}")
            self.stdout.write(f"    Address: {nearest.address}")
            self.stdout.write(f"    Distance: {nearest.distance.km:.2f} km")

            # Show top 3
            if count > 1:
                self.stdout.write(f"\n  Other nearby warehouses:")
                for warehouse in nearby_warehouses[1:4]:
                    self.stdout.write(
                        f"    - {warehouse.name} ({warehouse.distance.km:.2f} km)"
                    )
        else:
            self.stdout.write(
                self.style.WARNING(f"  ⚠ No warehouses found within {radius} km")
            )
            self.stdout.write(
                f"  Total warehouses in database: {Warehouse.objects.count()}"
            )
            self.stdout.write(
                f"  Active & approved: {Warehouse.objects.filter(is_active=True, is_approved=True).count()}"
            )

    def benchmark_query(self, lat, lon, radius, iterations=5):
        """Benchmark query performance"""
        import time

        self.stdout.write(
            self.style.WARNING(
                f"\nBenchmarking query performance ({iterations} iterations)..."
            )
        )

        user_location = Point(lon, lat, srid=4326)
        times = []

        for i in range(iterations):
            start_time = time.time()

            nearby_warehouses = (
                Warehouse.objects.filter(
                    location__isnull=False,
                    is_active=True,
                    is_approved=True,
                    location__distance_lte=(user_location, Distance(km=radius)),
                )
                .annotate(distance=DistanceFunc("location", user_location))
                .order_by("distance")[:1]
            )

            # Force query execution
            list(nearby_warehouses)

            elapsed = (time.time() - start_time) * 1000  # Convert to ms
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        self.stdout.write(f"\n  Performance metrics:")
        self.stdout.write(f"    Average query time: {avg_time:.2f} ms")
        self.stdout.write(f"    Min query time: {min_time:.2f} ms")
        self.stdout.write(f"    Max query time: {max_time:.2f} ms")

        if avg_time < 50:
            self.stdout.write(self.style.SUCCESS("  ✓ Excellent performance (< 50ms)"))
        elif avg_time < 200:
            self.stdout.write(self.style.SUCCESS("  ✓ Good performance (< 200ms)"))
        else:
            self.stdout.write(
                self.style.WARNING(f"  ⚠ Performance could be improved (> 200ms)")
            )
