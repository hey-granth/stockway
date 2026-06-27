import uuid
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point

User = get_user_model()


class Command(BaseCommand):
    help = "Seed load test users and associated data"

    def handle(self, *args, **options):
        test_users = [
            ("shopkeeper@test.local", "SHOPKEEPER"),
            ("warehouse@test.local", "WAREHOUSE_MANAGER"),
            ("rider@test.local", "RIDER"),
            ("admin@test.local", "ADMIN"),
        ]

        created_users = {}

        for email, role in test_users:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "role": role,
                    "is_active": True,
                    "is_staff": (role == "ADMIN"),
                    "is_superuser": (role == "ADMIN"),
                },
            )
            if not created:
                user.role = role
                if role == "ADMIN":
                    user.is_staff = True
                    user.is_superuser = True
            if not user.supabase_uid:
                user.supabase_uid = str(user.id) if user.id else str(uuid.uuid4())
            user.set_password("Test1234!")
            user.save()
            created_users[role] = user
            self.stdout.write(
                self.style.SUCCESS(f"Successfully seeded user {email} with role {role}")
            )

        # Seed Warehouse for WAREHOUSE_MANAGER
        from warehouses.models import Warehouse
        wh_user = created_users.get("WAREHOUSE_MANAGER")
        if wh_user:
            warehouse, _ = Warehouse.objects.get_or_create(
                id=1,
                defaults={
                    "admin": wh_user,
                    "name": "Default Test Warehouse",
                    "address": "123 Test Street",
                    "contact_number": "1234567890",
                    "location": Point(77.2090, 28.6139, srid=4326),
                    "is_active": True,
                    "is_approved": True,
                },
            )
            if warehouse.admin != wh_user or not warehouse.is_approved:
                warehouse.admin = wh_user
                warehouse.is_approved = True
                warehouse.is_active = True
                warehouse.save()

            # Seed Item in Warehouse
            from inventory.models import Item
            Item.objects.get_or_create(
                id=1,
                defaults={
                    "warehouse": warehouse,
                    "name": "Default Test Item",
                    "sku": "SKU-TEST-001",
                    "description": "Initial test item",
                    "category": "test",
                    "price": "99.99",
                    "quantity": 100,
                },
            )

            # Seed Rider Profile for RIDER
            rider_user = created_users.get("RIDER")
            if rider_user:
                from riders.models import Rider
                Rider.objects.get_or_create(
                    user=rider_user,
                    defaults={
                        "warehouse": warehouse,
                        "status": "available",
                        "availability": "available",
                        "current_location": Point(77.2090, 28.6139, srid=4326),
                    },
                )

        # Seed Shopkeeper Profile for SHOPKEEPER
        sk_user = created_users.get("SHOPKEEPER")
        if sk_user:
            from accounts.models import ShopkeeperProfile
            ShopkeeperProfile.objects.get_or_create(
                user=sk_user,
                defaults={
                    "shop_name": "Test Shop",
                    "shop_address": "456 Market Road",
                    "is_verified": True,
                    "location": Point(77.2090, 28.6139, srid=4326),
                },
            )
