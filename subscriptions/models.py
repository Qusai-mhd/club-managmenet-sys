import pytz
from django.conf import settings
from django.db import models
from django.db.models import Sum, F
from django.utils import timezone


# Create your models here.
class SportCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Division(models.Model):
    category = models.ForeignKey(SportCategory, on_delete=models.CASCADE)

    name = models.CharField(max_length=100)
    default_month_price = models.DecimalField(max_digits=5, decimal_places=2)

    suspended = models.BooleanField(default=False)

    # You can reference the training_days from the Division model with the related_name attribute
    # (e.g. division.training_days.all()).

    # You can reference the TrainingSessionRecord model from the Division model with the related_name attribute
    # (e.g. division.training_sessions.all()).

    def __str__(self):
        return str(self.category) + ' - ' + self.name


class TrainingWeekDay(models.Model):
    WEEKDAY_CHOICES = (
        ('الأحد', 'الأحد'),
        ('الاثنين', 'الاثنين'),
        ('الثلاثاء', 'الثلاثاء'),
        ('الأربعاء', 'الأربعاء'),
        ('الخميس', 'الخميس'),
        ('الجمعة', 'الجمعة'),
        ('السبت', 'السبت'),
    )
    day = models.CharField(max_length=10, choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    division = models.ForeignKey(Division, related_name='training_days', on_delete=models.CASCADE)

    def __str__(self):
        return self.day + ' - ' + str(self.division)


class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, null=True, related_name='subscriptions')
    # You can reference the SubscriptionPeriod model from the Subscription model with the related_name attribute
    # (e.g. subscription.subscription_periods.all()).

    class Meta:
        permissions = [
            ("change_subs_price", "بإمكانه تغيير السعر"),
        ]

    def __str__(self):
        return f'{self.user} - {self.division}'

    def make_payment(self, amount):
        invoice = Invoice.objects.create(subscription=self,
                                         total_price=self.total_due_payment_property,
                                         time=timezone.now().astimezone(pytz.timezone('Asia/Riyadh')),
                                         paid=0,
                                         action='تسديد دفعة')
        invoice_paid_amount = 0

        periods = self.subscription_periods.all()
        for period in periods:
            if period.paid_amount < period.price:
                remaining_amount = period.price - period.paid_amount
                if amount >= remaining_amount:
                    period.paid_amount = period.price
                    period.save()

                    invoice_paid_amount += remaining_amount
                    amount -= remaining_amount

                elif amount < remaining_amount and amount != 0:
                    period.paid_amount += amount
                    period.save()

                    invoice_paid_amount += amount
                    amount = 0
                else:
                    break
        if invoice_paid_amount != 0:
            invoice.paid = invoice_paid_amount
            invoice.save()

    @property
    def total_due_payment_property(self):
        total_due = self.subscription_periods.aggregate(
            total_due=Sum(F('price') - F('paid_amount'))
        )['total_due']
        return total_due or 0

    @property
    def most_recent_period(self):
        return self.subscription_periods.all().order_by('-end_date').first()


class SubscriptionPeriod(models.Model):
    subscription = models.ForeignKey(Subscription, related_name='subscription_periods', on_delete=models.CASCADE)

    start_date = models.DateField()
    end_date = models.DateField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return f'{self.end_date} - {self.start_date} - {self.subscription}'


class TrainingSessionRecord(models.Model):
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, related_name='training_sessions', null=True)
    date = models.DateField()

    # You can reference the individual_records from the TrainingSessionRecord model with the related_name attribute
    # (e.g. training_session_record.individual_records.all()).

    def __str__(self):
        return f'{self.division} - {self.date}'


class IndividualAttendanceRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    training_session_record = models.ForeignKey(TrainingSessionRecord, on_delete=models.CASCADE, related_name='individual_records')
    attended = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user} - {self.training_session_record}'


class Invoice(models.Model):
    action_choices = (('اشتراك جديد', 'اشتراك جديد'),
                      ('تسديد دفعة', 'تسديد دفعة'),
                      ('تمديد اشتراك', 'تمديد اشتراك'))

    subscription = models.ForeignKey(Subscription,related_name='invoices', on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=5, decimal_places=2)
    paid = models.DecimalField(max_digits=5, decimal_places=2)
    time = models.DateTimeField()
    action = models.CharField(max_length=100, choices=action_choices)

    def __str__(self):
        return f'{self.subscription} - {self.id}'








