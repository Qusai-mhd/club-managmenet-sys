from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.FacilityCategory)
admin.site.register(models.Facility)
admin.site.register(models.TimeSlot)
admin.site.register(models.Reservation)

