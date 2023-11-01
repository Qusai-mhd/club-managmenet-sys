from datetime import datetime
import calendar

from django.db import models
from django.db.models import OuterRef, Subquery, Sum, F
from django.utils import timezone

from subscriptions.models import SubscriptionPeriod, Invoice


def add_months(input_date, num_months):
    year = input_date.year + (input_date.month + num_months - 1) // 12
    month = (input_date.month + num_months - 1) % 12 + 1

    # Calculate the day, ensuring it's valid for the new month
    max_day = min(input_date.day, calendar.monthrange(year, month)[1])
    new_date = datetime(year, month, max_day).date()

    return new_date


def get_confirmed_subscription_queryset_from_params(queryset, params):
    params = validate_subscription_search_params(params)

    # First, annotate each Subscription with the latest end_date
    queryset = queryset.annotate(
        latest_end_date=Subquery(
            SubscriptionPeriod.objects.filter(
                subscription=OuterRef('pk')
            ).order_by('-end_date').values('end_date')[:1]
        )
    )

    # Define a subquery to calculate the total paid_amount for each subscription
    total_paid_amount_subquery = SubscriptionPeriod.objects.filter(
        subscription=OuterRef('pk')
    ).values('subscription').annotate(
        total_duee_amount=Sum(F('price') - F('paid_amount'))
    ).values('total_duee_amount')[:1]

    # Annotate the subscriptions with the total due payment
    queryset = queryset.annotate(
        total_due_payment=Subquery(total_paid_amount_subquery,
                                   output_field=models.DecimalField(max_digits=5, decimal_places=2))
    )

    # Annotate with the latest invoice of the subscription
    latest_invoice_subquery = Invoice.objects.filter(
        subscription=OuterRef('pk')
    ).order_by('-time').values('id')[:1]

    queryset = queryset.annotate(
        latest_invoice_id=Subquery(latest_invoice_subquery, output_field=models.IntegerField())
    )

    queryset = queryset.order_by('latest_end_date')

    if params['user'] is not None:
        queryset = queryset.filter(user=params['user'])

    # filter by division
    if params['division'] is not None:
        queryset = queryset.filter(division=params['division'])

    # filter by category
    if params['sportCategory'] is not None:
        queryset = queryset.filter(division__category=params['sportCategory'])

    current_date = timezone.now().date()

    if params['expired'] == 'yes':
        queryset = queryset.filter(latest_end_date__lt=current_date)

    elif params['expired'] == 'no':
        queryset = queryset.filter(latest_end_date__gte=current_date)

    return queryset


def validate_subscription_search_params(params):
    validated_params = {}

    objectNames = ['user', 'sportCategory', 'division']

    for objectName in objectNames:
        if objectName in params:
            try:
                objectId = int(params[objectName])
                validated_params[objectName] = objectId
            except (ValueError, TypeError):
                validated_params[objectName] = None
        else:
            validated_params[objectName] = None

    if 'expired' in params and (params['expired'] in ['yes', 'no', 'all']):
        validated_params['expired'] = params['expired']
    else:
        validated_params['expired'] = 'all'

    return validated_params
