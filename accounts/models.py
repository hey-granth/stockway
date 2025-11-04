from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.contrib.gis.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""

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
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="SHOPKEEPER")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

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
