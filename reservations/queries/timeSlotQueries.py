from django.db.models.query import QuerySet
from django.contrib.auth import get_user_model

from reservations import models


def get_free_slots(facility: models.Facility, date: str) -> QuerySet:
    """
    Get all the free slots for a given facility in a given day

    :param facility: A Facility object.
    :param date: A string date (YYYY-MM-dd)
    :return: A QuerySet object, with all the free TimeSlots
    """
    return models.TimeSlot.objects.filter(facility=facility).exclude(reservation__day=date)


def get_weekly_free_slots(facility: models.Facility, initial_date: str, weeksNum: int) -> QuerySet:
    """
    Get all time slots that are free for a given facility in a given day for a given number of weeks
    Ex: to get the free slots on Mondays for 3 weeks starting from 2023-08-21, call:
        get_weekly_free_slots(facility, '2023-08-21', 3)

    :param facility: A Facility object.
    :param initial_date: A string date (YYYY-MM-dd)
    :param weeksNum: An integer number of weeks
    """

    from reservations.utilities import get_dates_of_weekdays

    dates = get_dates_of_weekdays(initial_date, weeksNum)

    # Get the slots that are free for all the dates
    return models.TimeSlot.objects.filter(facility=facility).exclude(reservation__day__in=dates)


def get_all_slots(facility: models.Facility) -> QuerySet:
    """
    Get all the slots (reserved and free) for a given facility category ordered by start time

    :param facility: A Facility object
    :return: A QuerySet object, with all the TimeSlots
    """
    return models.TimeSlot.objects.filter(facility=facility).order_by('start_time')


def get_all_facilities() -> QuerySet:
    """
    Get all the facilities

    :return: A QuerySet object, with all the Facilities
    """
    return models.Facility.objects.all()


def get_all_customers() -> QuerySet:
    """
    Get all the customers
    :return: A QuerySet object, with all the customers
    """
    return get_user_model().objects.filter(is_staff=False, confirmed=True)
