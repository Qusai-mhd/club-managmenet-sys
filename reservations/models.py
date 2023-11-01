import os

from django.db import models
from django.conf import settings
from django.urls import reverse
from django.core.exceptions import ValidationError


class FacilityCategory(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


# Create your models here.
class Facility(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(FacilityCategory, on_delete=models.SET_NULL, null=True)
    default_price = models.IntegerField(default=0)
    image = models.ImageField(upload_to='facilities/', blank=True, null=True)
    color = models.CharField(max_length=7, default='#000000')
    suspended = models.BooleanField(default=False)

    def get_absolute_url(self):
        return reverse('reservations:get-facility', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name


class TimeSlot(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()

    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return str(self.start_time.strftime('%I:%M %p')) + ' => ' + str(self.end_time.strftime('%I:%M %p'))

    def clean(self):
        super().clean()
        if self.start_time >= self.end_time:

            # There is a special case where the start time is right before midnight and the end time is right after
            if not ((22 <= self.start_time.hour < 24) and (0 <= self.end_time.hour <= 2)):
                raise ValidationError('وقت البداية يجب أن يكون قبل وقت النهاية')


class Reservation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.SET_NULL, null=True)

    day = models.DateField()
    price = models.IntegerField()

    def __str__(self):
        if self.facility and self.user:
            return f'حجز {self.user} لـ {self.facility} يوم {self.day}'

        elif self.facility:
            return f'حجز {self.facility} يوم {self.day}'

        elif self.user:
            return f'حجز {self.user} يوم {self.day}'

        else:
            return f'حجز يوم {self.day}'

    class Meta:
        permissions = [
            ("change_price", "بإمكانه تغيير السعر"),
            ("create_report", "بإمكانه إنشاء تقرير")
        ]
