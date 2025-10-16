from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
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

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.phone_number


class ShopkeeperProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shopkeeper_profile"
    )
    shop_name = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    def __str__(self):
        return self.shop_name
