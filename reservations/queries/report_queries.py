from reservations.models import Reservation
from django.db.models import Count, Sum, Q, F


def get_reservations_between_dates(date1, date2):
    return Reservation.objects.filter(day__range=[date1, date2])


def get_most_paying_users(reservations_queryset, num_of_users=5):
    """
    this returns a list of dictionaries, like the following:

    < QuerySet[{'user__full_name': 'Omar', 'user__phone': '0530000001', 'user__gender': 'M', 'res_count': 23,
                   'total_unpaid': 5092, 'total_paid': 2314, 'total_money': 7406},
                  {'user__full_name': 'Omar 2', 'user__phone': '0530000000','user__gender': 'M', 'res_count': 2,
                   'total_unpaid': 0, 'total_paid': 800, 'total_money': 800}, etc... ] >
    """

    return (reservations_queryset
            .values('user__full_name', 'user__phone', 'user__gender')
            .annotate(reservations_count=Count('user'))
            .annotate(total_paid=Sum('price', default=0))
            .order_by('-total_paid')
            [:num_of_users]
            )


def get_facilities_report(queryset):
    # get all the facilities ordered by the income they made
    # this returns a list of dictionaries, like the following:
    # < QuerySet[{'facility__name': 'Facility 1', 'reservations_count': 23, 'income_generated': 5092},
    #            {'facility__name': 'Facility 2', 'reservations_count': 2, 'income_generated': 800}, etc... ] >

    return (queryset
            .values('facility__name')
            .annotate(reservations_count=Count('facility'))
            .annotate(income_generated=Sum('price', default=0))
            .order_by('-income_generated'))


def get_categories_report(queryset):
    # get all the categories ordered by the income they made
    # this returns a list of dictionaries, like the following:
    # < QuerySet[{'facility__category__name': 'Category 1', 'reservations_count': 23, 'income_generated': 5092},

    return (queryset
            .values('facility__category__name')
            .annotate(reservations_count=Count('facility__category'))
            .annotate(income_generated=Sum('price', default=0))
            .order_by('-income_generated'))


def get_gender_report(queryset):
    # summarize the reservations based on the gender of the customer
    # this returns a list of dictionaries, like the following:
    # < QuerySet[{'user__gender': 'M', 'reservations_count': 23, 'customers_count':4, 'income_generated': 5092},

    return (queryset.values('user__gender')
            .annotate(reservations_count=Count('user__gender'))
            .annotate(customers_count=Count('user', distinct=True))
            .annotate(income_generated=Sum('price', default=0))
            .order_by('-income_generated'))



def get_summary_report(reservations_queryset):
    # get the total number of reservations, the number of unique users, the total paid and the total unpaid
    # this returns a dictionary, like the following:
    # {'reservations_count': 25, 'users_count': 2, 'total_paid': 3114, 'total_unpaid': 5092}

    return (reservations_queryset
            .aggregate(reservations_count=Count('id'),
                       users_count=Count('user', distinct=True),
                       total_paid=Sum('price', default=0)))


def get_report_info(date1, date2):
    reservations = get_reservations_between_dates(date1, date2)

    return {
        'reservations_report': get_summary_report(reservations),
        'facilities_report': get_facilities_report(reservations),
        'categories_report': get_categories_report(reservations),
        'customers_report': get_most_paying_users(reservations, 5),
        'gender_report': get_gender_report(reservations)
    }
