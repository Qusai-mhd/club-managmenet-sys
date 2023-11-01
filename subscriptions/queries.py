from django.db.models import Sum, Count, Q, DecimalField, OuterRef, Subquery
from django.db.models.query import QuerySet
from django.contrib.auth import get_user_model

from subscriptions.models import IndividualAttendanceRecord, SubscriptionPeriod, Division


def get_all_customers() -> QuerySet:
    """
    Get all the customers
    :return: A QuerySet object, with all the customers
    """
    return get_user_model().objects.filter(is_staff=False, confirmed=True)


def new_subs_report(period_queryset):
    return (period_queryset.aggregate(new_subs_count=Count('id'),
                                      total_prices=Sum('price'),
                                      total_paid_amount=Sum('paid_amount')))


def division_report(start_date, end_date):
    filtered_periods_subquery = SubscriptionPeriod.objects.filter(
        subscription__division=OuterRef('pk'),
        start_date__gte=start_date,
        start_date__lte=end_date
    ).values('subscription__division').annotate(total_price=Sum('price')).values('total_price')

    return Division.objects.annotate(
        subscriptions_count=Count('subscriptions', distinct=True,
                                  filter=Q(subscriptions__subscription_periods__start_date__gte=start_date,
                                           subscriptions__subscription_periods__start_date__lte=end_date)),
        number_of_sessions=Count('training_sessions', distinct=True,
                                 filter=Q(training_sessions__date__gte=start_date,
                                          training_sessions__date__lte=end_date)),
        income_generated=Subquery(filtered_periods_subquery, output_field=DecimalField(max_digits=10, decimal_places=2))
    )


def training_sessions_report(start_date, end_date):
    queryset = (IndividualAttendanceRecord.objects.filter(training_session_record__date__gte=start_date,
                                                          training_session_record__date__lte=end_date)
                .aggregate(attended_count=Count('id', filter=Q(attended=True)),
                           absent_count=Count('id', filter=Q(attended=False)),
                           sessions_count=Count('training_session_record__id', distinct=True)))
    return queryset


def get_summary_report(start_date, end_date):
    periods = SubscriptionPeriod.objects.filter(start_date__gte=start_date, start_date__lte=end_date)

    return {
        'new_subs_report': new_subs_report(periods),
        'division_report': division_report(start_date,end_date),
        'training_sessions_report': training_sessions_report(start_date, end_date)
    }
