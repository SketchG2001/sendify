from cryptography.fernet import Fernet
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = CustomUserManager()

cipher = Fernet(settings.ENCRYPTION_KEY.encode())

class Configurations(models.Model):
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    email = models.EmailField(unique=True)
    _app_password = models.BinaryField()
    is_active = models.BooleanField(default=True)

    @property
    def app_password(self):
        """Decrypt password when accessed"""
        return cipher.decrypt(self._app_password).decode()

    @app_password.setter
    def app_password(self, raw_password):
        """Encrypt before saving"""
        self._app_password = cipher.encrypt(raw_password.encode())

    def save(self, *args, **kwargs):
        if self.is_active:
            Configurations.objects.filter(
                user=self.user, is_active=True
            ).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.email} ({'Active' if self.is_active else 'Inactive'})"
