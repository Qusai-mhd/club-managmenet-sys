from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from .validators import validate_phone

# The Docs for what we did here:
# https://docs.djangoproject.com/en/4.2/topics/auth/customizing/#specifying-a-custom-user-model


class RSUserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.is_staff = False
        user.save()
        return user

    def create_superuser(self, phone, password, **extra_fields):
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        return user


class RSUser(AbstractBaseUser, PermissionsMixin):
    GENDER_CHOICES = [
        ('M', 'ذكر'),
        ('F', 'أنثى'),
    ]
    phone = models.CharField(max_length=10, unique=True, validators=[validate_phone])
    email = models.EmailField(null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    full_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    birth_date = models.DateField(null=True, blank=True)
    confirmed = models.BooleanField(default=True)

    objects = RSUserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['gender', 'full_name']
    EMAIL_FIELD = 'email'

    def get_full_name(self):
        return self.full_name

    def __str__(self):
        return self.full_name
