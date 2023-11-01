from django.contrib import admin

from subscriptions import models

# Register your models here.
admin.site.register(models.Subscription)
admin.site.register(models.Division)
admin.site.register(models.TrainingWeekDay)
admin.site.register(models.SportCategory)
admin.site.register(models.SubscriptionPeriod)
admin.site.register(models.TrainingSessionRecord)
admin.site.register(models.IndividualAttendanceRecord)
admin.site.register(models.Invoice)

