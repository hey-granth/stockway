from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.contrib.gis.db import models
from django.utils import timezone


class ActiveUserManager(BaseUserManager):
    """
    Manager that returns only active (non-deleted) users by default.
    Used as the default manager for most queries.
    """

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True, deleted_at__isnull=True)

    def create_user(self, email=None, phone_number=None, password=None, **extra_fields):
        """Create and save a regular user with email"""
        if not email and not phone_number:
            raise ValueError("Either email or phone number must be set")

        if email:
            email = self.normalize_email(email)

        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user = self.model(email=email, phone_number=phone_number, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email=None, phone_number=None, password=None, **extra_fields
    ):
        """Create and save a superuser with email"""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "ADMIN")

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            email=email, phone_number=phone_number, password=password, **extra_fields
        )


class UserManager(BaseUserManager):
    """
    Manager that returns ALL users including soft-deleted ones.
    Use this for admin views and historical data queries.
    """

    def get_queryset(self):
        return super().get_queryset()

    def create_user(self, email=None, phone_number=None, password=None, **extra_fields):
        """Create and save a regular user with email"""
        if not email and not phone_number:
            raise ValueError("Either email or phone number must be set")

        if email:
            email = self.normalize_email(email)

        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user = self.model(email=email, phone_number=phone_number, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email=None, phone_number=None, password=None, **extra_fields
    ):
        """Create and save a superuser with email"""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "ADMIN")

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            email=email, phone_number=phone_number, password=password, **extra_fields
        )


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model with email-based authentication"""

    ROLE_CHOICES = [
        ("PENDING", "Pending Approval"),
        ("SHOPKEEPER", "Shopkeeper"),
        ("RIDER", "Rider"),
        ("WAREHOUSE_MANAGER", "Warehouse Manager"),
        ("ADMIN", "Admin"),
    ]

    phone_number = models.CharField(
        max_length=20, unique=True, null=True, blank=True, db_index=True
    )
    supabase_uid = models.CharField(
        max_length=255, unique=True, null=True, blank=True, db_index=True
    )
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="PENDING")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    profile_image_url = models.TextField(null=True, blank=True)

    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    # Soft delete field
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    # Managers
    objects = ActiveUserManager()  # Default manager - excludes soft-deleted users
    all_objects = UserManager()  # Includes all users for admin/historical queries

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email or self.phone_number or str(self.id)

    def get_full_name(self):
        return self.full_name or self.email

    def get_short_name(self):
        return self.email

    @property
    def is_deleted(self):
        """Check if user has been soft deleted"""
        return self.deleted_at is not None

    def soft_delete(self):
        """
        Soft delete the user by setting is_active=False and deleted_at timestamp.
        Does not actually remove the database record.
        """
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_active", "deleted_at"])

    def restore(self):
        """
        Restore a soft-deleted user by clearing deleted_at and setting is_active=True.
        """
        self.is_active = True
        self.deleted_at = None
        self.save(update_fields=["is_active", "deleted_at"])

    def has_dependent_data(self):
        """
        Check if user has any dependent business data that would prevent hard deletion.
        Returns tuple of (has_dependencies, details_dict)
        """
        dependencies = {}

        # Check for warehouses (if user is warehouse admin)
        if hasattr(self, "warehouses"):
            warehouse_count = self.warehouses.count()
            if warehouse_count > 0:
                dependencies["warehouses"] = warehouse_count

        # Check for orders (as shopkeeper)
        if hasattr(self, "orders"):
            order_count = self.orders.count()
            if order_count > 0:
                dependencies["orders"] = order_count

        # Check for shopkeeper profile
        if hasattr(self, "shopkeeper_profile"):
            try:
                if self.shopkeeper_profile:
                    dependencies["shopkeeper_profile"] = 1
            except ShopkeeperProfile.DoesNotExist:
                pass

        # Check for deliveries (as rider)
        if hasattr(self, "deliveries"):
            delivery_count = self.deliveries.count()
            if delivery_count > 0:
                dependencies["deliveries"] = delivery_count

        # Check for rider profile
        if hasattr(self, "rider_profile"):
            try:
                if self.rider_profile:
                    dependencies["rider_profile"] = 1
            except Exception:
                pass

        return (len(dependencies) > 0, dependencies)


class ShopkeeperProfile(models.Model):
    """Extended profile for shopkeeper users"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="shopkeeper_profile"
    )
    shop_name = models.CharField(max_length=255, default="")
    shop_address = models.TextField(default="")
    location = models.PointField(geography=True, null=True, blank=True)
    gst_number = models.CharField(max_length=15, blank=True, default="")
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "shopkeeper_profiles"
        verbose_name = "Shopkeeper Profile"
        verbose_name_plural = "Shopkeeper Profiles"

    def __str__(self):
        return f"{self.shop_name} - {self.user.email or self.user.phone_number}"
