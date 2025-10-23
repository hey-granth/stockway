"""
Django management command to test Supabase integration.

Usage:
    python manage.py test_supabase
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from configs.config import Config
from configs.supabase_storage import SupabaseStorage
import jwt
from datetime import timedelta
from django.utils.timezone import now


class Command(BaseCommand):
    help: str = "Test Supabase integration (Auth + Storage + DB)"

    def handle(self, *args, **options) -> None:
        self.stdout.write(
            self.style.SUCCESS("\n=== Supabase Integration Diagnostic ===\n")
        )

        # Test 1: Check configuration
        self.stdout.write(self.style.WARNING("1. Checking Configuration..."))
        self.check_config()

        # Test 2: Test JWT verification
        self.stdout.write(self.style.WARNING("\n2. Testing JWT Token Verification..."))
        self.test_jwt()

        # Test 3: Test Storage connection
        self.stdout.write(self.style.WARNING("\n3. Testing Storage Connection..."))
        self.test_storage()

        # Test 4: Test Database connection
        self.stdout.write(self.style.WARNING("\n4. Testing Database Connection..."))
        self.test_database()

        self.stdout.write(self.style.SUCCESS("\n=== Diagnostic Complete ===\n"))

    def check_config(self) -> None:
        """Check if all required Supabase configs are set."""
        configs: dict[str, str] = {
            "SUPABASE_URL": Config.SUPABASE_URL,
            "SUPABASE_KEY": Config.SUPABASE_KEY,
            "SUPABASE_SERVICE_KEY": Config.SUPABASE_SERVICE_KEY,
            "SUPABASE_JWT_SECRET": Config.SUPABASE_JWT_SECRET,
        }

        all_set: bool = True
        for key, value in configs.items():
            if value and value != f"your-{key.lower().replace('_', '-')}-here":
                self.stdout.write(self.style.SUCCESS(f"   ✓ {key}: Configured"))
            else:
                self.stdout.write(self.style.ERROR(f"   ✗ {key}: Not configured"))
                all_set = False

        if all_set:
            self.stdout.write(self.style.SUCCESS("\n   All configurations are set!"))
        else:
            self.stdout.write(
                self.style.WARNING(
                    "\n   Please update .env with your Supabase credentials"
                )
            )

    def test_jwt(self):
        """Test JWT token generation and verification."""
        if not Config.SUPABASE_JWT_SECRET:
            self.stdout.write(self.style.ERROR("   ✗ JWT secret not configured"))
            return

        try:
            # Create a test JWT token
            test_payload = {
                "sub": "test-user-id-12345",
                "email": "test@example.com",
                "phone": "1234567890",
                "aud": "authenticated",
                "exp": now() + timedelta(hours=1),
                "iat": now(),
            }

            test_token = jwt.encode(
                test_payload, Config.SUPABASE_JWT_SECRET, algorithm="HS256"
            )

            # Verify the token
            decoded = jwt.decode(
                test_token,
                Config.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
            )

            self.stdout.write(self.style.SUCCESS("   ✓ JWT token generation: OK"))
            self.stdout.write(self.style.SUCCESS("   ✓ JWT token verification: OK"))
            self.stdout.write(
                f"   Token payload: sub={decoded['sub']}, email={decoded.get('email')}"
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ✗ JWT test failed: {str(e)}"))

    def test_storage(self) -> None:
        """Test Supabase Storage connection."""
        if not Config.SUPABASE_URL or not Config.SUPABASE_SERVICE_KEY:
            self.stdout.write(
                self.style.ERROR("   ✗ Storage credentials not configured")
            )
            return

        if Config.SUPABASE_URL:
            self.stdout.write(
                self.style.WARNING(
                    "   ⚠ Using placeholder URL - update .env with real Supabase project URL"
                )
            )
            return

        try:
            # Try to get storage client
            client = SupabaseStorage.get_client()
            self.stdout.write(self.style.SUCCESS("   ✓ Storage client initialized"))

            # List buckets (if accessible)
            try:
                buckets = client.storage.list_buckets()
                self.stdout.write(self.style.SUCCESS("   ✓ Storage connection: OK"))
                if buckets:
                    self.stdout.write(f"   Found {len(buckets)} storage bucket(s)")
                else:
                    self.stdout.write(
                        "   No buckets found (you may need to create them)"
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"   ⚠ Could not list buckets: {str(e)}")
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ✗ Storage test failed: {str(e)}"))

    def test_database(self) -> None:
        """Test database connection."""
        from django.db import connection

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]

            self.stdout.write(self.style.SUCCESS("   ✓ Database connection: OK"))

            if settings.USE_SUPABASE_DB:
                self.stdout.write(
                    self.style.SUCCESS("   Using Supabase Managed Postgres")
                )
                self.stdout.write(f"   Host: {Config.SUPABASE_DB_HOST}")
            else:
                self.stdout.write(self.style.SUCCESS("   Using Local Postgres"))
                self.stdout.write(f"   Host: {Config.DB_HOST}")

            self.stdout.write(f"   PostgreSQL version: {version.split(',')[0]}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ✗ Database test failed: {str(e)}"))


# This file makes the management directory a Python package
