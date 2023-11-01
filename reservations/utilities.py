from datetime import datetime, timedelta
import pytz

from reservations.models import Reservation, Facility, TimeSlot


def get_reservation_queryset_from_params(queryset, params):
    """
    Get a queryset of reservations from a dictionary of parameters
    Ex: to get all reservations for a given facility, call:
        get_reservation_queryset_from_params({'facility': facility})

    :param queryset: A queryset of reservations
    :param params: A dictionary of parameters
    :return: A queryset of reservations
    """
    params = validate_reservation_search_params(params)

    queryset = queryset.order_by('-day', '-time_slot__start_time')

    if params['searchByFacility'] == 'facility':
        # filter by facility
        if params['facility'] is not None:
            queryset = queryset.filter(facility=params['facility'])

    elif params['searchByFacility'] == 'category':
        # filter by category
        if params['category'] is not None:
            queryset = queryset.filter(facility__category=params['category'])

    # filter by user
    if params['user'] is not None:
        queryset = queryset.filter(user=params['user'])

    if params['gender'] == 'male':
        queryset = queryset.filter(user__gender='M')

    elif params['gender'] == 'female':
        queryset = queryset.filter(user__gender='F')

    if params['searchByDay'] == 'exact':
        if params['day'] is not None:
            queryset = queryset.filter(day=params['day'])

    elif params['searchByDay'] == 'range':
        if params['dayFrom'] is not None and params['dayTo'] is not None:
            queryset = queryset.filter(day__range=[params['dayFrom'], params['dayTo']])

    elif params['searchByDay'] == 'before':
        if params['day'] is not None:
            queryset = queryset.filter(day__lte=params['day'])

    elif params['searchByDay'] == 'after':
        if params['day'] is not None:
            queryset = queryset.filter(day__gte=params['day'])

    if params['searchByPrice'] == 'exact':
        if params['price'] is not None:
            queryset = queryset.filter(price=params['price'])

    elif params['searchByPrice'] == 'range':
        if params['priceFrom'] is not None and params['priceTo'] is not None:
            queryset = queryset.filter(price__range=[params['priceFrom'], params['priceTo']])

    elif params['searchByPrice'] == 'less':
        if params['price'] is not None:
            queryset = queryset.filter(price__lt=params['price'])

    elif params['searchByPrice'] == 'greater':
        if params['price'] is not None:
            queryset = queryset.filter(price__gt=params['price'])

    return queryset


def validate_reservation_search_params(params):
    validated_params = {}

    objectNames = ['facility', 'category', 'user']

    for objectName in objectNames:
        if objectName in params:
            try:
                objectId = int(params[objectName])
                validated_params[objectName] = objectId
            except (ValueError, TypeError):
                validated_params[objectName] = None
        else:
            validated_params[objectName] = None

    if 'searchByFacility' in params and (params['searchByFacility'] in ['facility', 'category']):
        validated_params['searchByFacility'] = params['searchByFacility']
    else:
        validated_params['searchByFacility'] = 'facility'

    if 'searchByPrice' in params and (params['searchByPrice'] in ['exact', 'range', 'less', 'greater']):
        validated_params['searchByPrice'] = params['searchByPrice']
    else:
        validated_params['searchByPrice'] = 'exact'

    if 'gender' in params and (params['gender'] in ['male', 'female', 'all']):
        validated_params['gender'] = params['gender']
    else:
        validated_params['gender'] = 'all'

    priceNames = ['price', 'priceFrom', 'priceTo']

    for priceName in priceNames:
        if priceName in params:
            try:
                price = float(params[priceName])
                validated_params[priceName] = price
            except (ValueError, TypeError):
                validated_params[priceName] = None
        else:
            validated_params[priceName] = None

    if 'searchByDay' in params and (params['searchByDay'] in ['exact', 'range', 'before', 'after']):
        validated_params['searchByDay'] = params['searchByDay']
    else:
        validated_params['searchByDay'] = 'exact'

    dateNames = ['day', 'dayFrom', 'dayTo']

    for dateName in dateNames:
        if dateName in params:
            try:
                date = datetime.strptime(params[dateName], '%Y-%m-%d').astimezone(pytz.timezone('Asia/Riyadh')).date()
                validated_params[dateName] = date
            except (ValueError, TypeError):
                validated_params[dateName] = None
        else:
            validated_params[dateName] = None

    return validated_params


def get_dates_of_weekdays(initial_date: str, weeksNum: int) -> list[datetime.date]:
    """
    Get a list of dates for a given initial date and number of weeks
    Ex: to get the dates of Mondays for 3 weeks starting from 2023-08-21, call:
        get_dates_of_weekdays('2023-08-21', 3)

    :param initial_date: A string date (YYYY-MM-dd)
    :param weeksNum: An integer number of weeks
    :return: A list of string dates (YYYY-MM-dd)
    """

    # check if initial_date is a string
    if isinstance(initial_date, str):
        # convert string date to date object
        initial_date = datetime.strptime(initial_date, '%Y-%m-%d').astimezone(pytz.timezone('Asia/Riyadh')).date()

    dates = []

    currentDate = initial_date

    for i in range(weeksNum):
        dates.append(currentDate)
        currentDate = currentDate + timedelta(days=7)
    return dates


def createMultipleReservations(facility, initialDay, user, time_slot, price, weeksNum):
    """
    Create multiple reservations for a given facility, user, time slot, price, is_paid, day and number of weeks

    :param facility: A Facility object
    :param user: A User object
    :param time_slot: A TimeSlot object
    :param price: A float price
    :param initialDay: A string date (YYYY-MM-dd)
    :param weeksNum: An integer number of weeks
    :return: A list of Reservation objects
    """

    reservations = []
    dates = get_dates_of_weekdays(initialDay, weeksNum)
    for date in dates:
        reservation = Reservation.objects.create(facility=facility, user=user, time_slot=time_slot, price=price,
                                                 day=date)
        reservation.save()
        reservations.append(reservation)
    return reservations


def get_next_seven_days(initial_date):
    """
    Get the names and dates of the next seven days for a given initial date
    """

    # check if initial_date is a string
    if isinstance(initial_date, str):
        # convert string date to date object
        initial_date = datetime.strptime(initial_date, '%Y-%m-%d').astimezone(pytz.timezone('Asia/Riyadh')).date()

    arabic_names = {'Saturday': 'السبت', 'Sunday': 'الأحد', 'Monday': 'الاثنين', 'Tuesday': 'الثلاثاء',
                    'Wednesday': 'الأربعاء', 'Thursday': 'الخميس', 'Friday': 'الجمعة'}
    days = []
    currentDate = initial_date

    days.append({'name': 'اليوم', 'date': currentDate.strftime('%Y-%m-%d')})
    currentDate = currentDate + timedelta(days=1)

    for i in range(7):
        day = {'name': arabic_names[currentDate.strftime('%A')], 'date': currentDate.strftime('%Y-%m-%d')}
        days.append(day)
        currentDate = currentDate + timedelta(days=1)
    return days


def get_facilities_and_slots(day):
    facilities = Facility.objects.all()
    facilities_and_slots = [{'facility_name': facility.name,
                             'free_slots': TimeSlot.objects.filter(facility=facility).exclude(reservation__day=day)
                             .order_by('start_time')}
                            for facility in facilities]
    return facilities_and_slots


def check_time_conflict(time_slot1, time_slot2):
    """
    Check if two time slots conflict with each other
    :param time_slot1: A TimeSlot object
    :param time_slot2: A TimeSlot object
    :return: True if the two time slots conflict with each other, False otherwise
    """
    if time_slot1.start_time < time_slot2.start_time < time_slot1.end_time:
        return True
    if time_slot1.start_time < time_slot2.end_time < time_slot1.end_time:
        return True
    if time_slot2.start_time < time_slot1.start_time < time_slot2.end_time:
        return True
    if time_slot2.start_time < time_slot1.end_time < time_slot2.end_time:
        return True
    return False
