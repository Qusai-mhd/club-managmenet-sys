import os

from django.core.exceptions import ValidationError
from django.db import models
from .validators import validate_tax_number, validate_commercial_register


# Create your models here.
class Organization(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    tax_number = models.CharField(max_length=15, validators=[validate_tax_number])
    commercial_register = models.CharField(max_length=14, validators=[validate_commercial_register])
    logo = models.ImageField(upload_to='organizationLogo/', blank=True, null=True)
    background = models.ImageField(upload_to='organizationBackground/', blank=True, null=True)

    def clean(self):
        super().clean()
        if not self.id and Organization.objects.exists():
            raise ValidationError('You cannot add more organizations.')
