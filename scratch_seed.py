import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from accounts.models import User
from warehouses.models import Warehouse
from inventory.models import Item
from django.contrib.gis.geos import Point

def seed():
    # Admin
    admin, _ = User.objects.get_or_create(email="admin@test.local", defaults={
        "role": "ADMIN",
        "is_superuser": True,
        "is_staff": True,
        "is_active": True,
        "supabase_uid": "admin-uid"
    })
    admin.set_password("password")
    admin.save()

    # Shopkeeper
    sk, _ = User.objects.get_or_create(email="shopkeeper@test.local", defaults={
        "role": "SHOPKEEPER",
        "is_active": True,
        "supabase_uid": "shopkeeper-uid"
    })
    sk.set_password("password")
    sk.save()

    # Rider
    rider, _ = User.objects.get_or_create(email="rider@test.local", defaults={
        "role": "RIDER",
        "is_active": True,
        "supabase_uid": "rider-uid"
    })
    rider.set_password("password")
    rider.save()

    # Warehouse Manager
    wm, _ = User.objects.get_or_create(email="warehouse@test.local", defaults={
        "role": "WAREHOUSE_MANAGER",
        "is_active": True,
        "supabase_uid": "warehouse-uid"
    })
    wm.set_password("password")
    wm.save()

    # Warehouse 1
    w, _ = Warehouse.objects.get_or_create(id=1, defaults={
        "name": "Test Warehouse",
        "admin": wm,
        "location": Point(0, 0),
        "is_active": True
    })

    # Sample Item
    Item.objects.get_or_create(id=1, defaults={
        "warehouse": w,
        "name": "Sample Item",
        "price": 10.00,
        "quantity": 100
    })
    
    print("Seed complete.")

if __name__ == "__main__":
    seed()
