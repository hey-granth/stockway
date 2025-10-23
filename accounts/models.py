from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.conf import settings


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("The Phone Number must be set")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.SUPER_ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractUser):
    username = None  # removing inherited username field so that phone number can be used as the username
    # was having issues in creating superuser without username field

    class Role(models.TextChoices):
        SHOPKEEPER = "SHOPKEEPER", "Shopkeeper"
        WAREHOUSE_ADMIN = "WAREHOUSE_ADMIN", "Warehouse Admin"
        RIDER = "RIDER", "Rider"
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"

    phone_number = models.CharField(max_length=15, unique=True)
    role = models.CharField(
        max_length=50,
        choices=Role.choices,
        default=Role.SHOPKEEPER,
    )
    is_verified = models.BooleanField(default=False)

    # Supabase integration field
    supabase_uid = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Supabase Auth UID for JWT authentication",
    )

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.phone_number


class ShopkeeperProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shopkeeper_profile",
    )
    shop_name = models.CharField(max_length=255, blank=True, default='')
    address = models.TextField(blank=True, default='')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    gst_number = models.CharField(max_length=50, blank=True, default='')
    license_number = models.CharField(max_length=50, blank=True, default='')
    onboarding_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.shop_name if self.shop_name else f"Profile for {self.user.phone_number}"

    def mark_onboarding_complete(self):
        """
        Mark onboarding as completed if all required fields are filled.
        Required: shop_name, address, latitude, longitude, and at least one of gst_number or license_number
        """
        if (
            self.shop_name
            and self.address
            and self.latitude is not None
            and self.longitude is not None
            and (self.gst_number or self.license_number)
        ):
            self.onboarding_completed = True
        else:
            self.onboarding_completed = False

    class Meta:
        verbose_name = "Shopkeeper Profile"
        verbose_name_plural = "Shopkeeper Profiles"
