from django.http import HttpResponseForbidden
from django.urls import reverse_lazy


def get_url_for_permission(user):
    if user.is_superuser:
        return reverse_lazy('users:staff-list')
    elif user.is_staff:
        if user.has_perm('reservations.add_reservation'):
            return reverse_lazy('reservations:home')
        elif user.has_perm('reservations.add_facility'):
            return reverse_lazy('reservations:facilities-list')
        elif user.has_perm('reservations.create_report'):
            return reverse_lazy('reservations:choose-report')
        elif user.has_perm('subscriptions.add_trainingsessionrecord'):
            return reverse_lazy('subscriptions:home')
        elif user.has_perm('subscriptions.add_subscription'):
            return reverse_lazy('subscriptions:search-subscriptions')
        elif user.has_perm('subscriptions.add_division'):
            return reverse_lazy('subscriptions:divisions-list')

    return None
