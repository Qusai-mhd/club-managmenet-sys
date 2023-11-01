import pytz
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DeleteView, ListView, TemplateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormMixin
from django.db.models import Q
from formtools.wizard.views import SessionWizardView

from reservations.forms import ReservationSearchForm, ReservationForm1, ReservationForm2, UpdateReservationForm1, \
    UpdateReservationForm2, WeeklyReservationForm1, WeeklyReservationForm2
from reservations.models import Reservation, TimeSlot
from reservations.queries import get_all_slots, get_weekly_free_slots, get_free_slots
from reservations.utilities import createMultipleReservations, get_reservation_queryset_from_params, \
    validate_reservation_search_params, get_next_seven_days, get_facilities_and_slots

from datetime import datetime, timedelta
from urllib.parse import urlencode


class FormListView(FormMixin, ListView):
    def get(self, request, *args, **kwargs):
        # From ProcessFormMixin
        form_class = self.get_form_class()
        self.form = self.get_form(form_class)

        # From BaseListView
        self.object_list = self.get_queryset()
        allow_empty = self.get_allow_empty()
        if not allow_empty and len(self.object_list) == 0:
            raise Http404("Empty list and '%(class_name)s.allow_empty' is False."
                          % {'class_name': self.__class__.__name__})

        context = self.get_context_data(object_list=self.object_list, form=self.form)
        return self.render_to_response(context)


class ReservationsListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'reservations.add_reservation'
    model = Reservation
    today = timezone.now().astimezone(pytz.timezone('Asia/Riyadh')).date()
    template_name = 'reservationsTemplates/reservations.html'

    today_queryset = Reservation.objects.filter(day=today).filter(
        Q(time_slot__end_time__gte=timezone.now().astimezone(pytz.timezone('Asia/Riyadh'))) | Q(time_slot__start_time__gte=timezone.now().astimezone(pytz.timezone('Asia/Riyadh'))))
    tomorrow = today + timedelta(days=1)
    tomorrow_queryset = Reservation.objects.filter(day=tomorrow, time_slot__start_time__lte='04:00:00')
    queryset = (today_queryset | tomorrow_queryset).order_by('day', 'time_slot__start_time')

    context_object_name = 'reservations'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.now().astimezone(pytz.timezone('Asia/Riyadh')).date()
        next_days = get_next_seven_days(today)

        context.update({'next_days': next_days, 'home_active': True})
        return context


class FreeSlotsView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'reservations.add_reservation'
    template_name = 'reservationsTemplates/freeSlots.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.now().astimezone(pytz.timezone('Asia/Riyadh')).date()
        next_days = get_next_seven_days(today)

        chosenDay = self.kwargs.get('day')

        # validate the day format
        try:
            datetime.strptime(chosenDay, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            raise Http404()

        facilities_and_slots = get_facilities_and_slots(chosenDay)

        context.update({'next_days': next_days, 'facilities_slots': facilities_and_slots, 'chosenDay': chosenDay,
                        'home_active': True})
        return context


class ReservationListFormView(LoginRequiredMixin, PermissionRequiredMixin, FormListView):
    permission_required = 'reservations.add_reservation'
    form_class = ReservationSearchForm
    model = Reservation
    template_name = 'reservationsTemplates/reservationsListForm.html'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        # get the URL get parameters
        params = self.request.GET

        return get_reservation_queryset_from_params(queryset, params)

    def get_initial(self):
        # get the URL get parameters
        params = self.request.GET

        params = validate_reservation_search_params(params)

        return params

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({'res_list_active': True})
        return context


class ReservationWizardView(LoginRequiredMixin, PermissionRequiredMixin, SessionWizardView):
    permission_required = 'reservations.add_reservation'
    form_list = [ReservationForm1, ReservationForm2]
    template_name = 'reservationsTemplates/create_reservation.html'

    def get_form_kwargs(self, step=None):
        if step != '1':
            return {}

        first_form_data = self.get_cleaned_data_for_step('0')
        facility = first_form_data.get('facility')
        day = first_form_data.get('day')
        price = facility.default_price

        kwargs = {'fac': facility, 'day': day, 'price': price}
        if self.request.user.has_perm('reservations.change_price'):
            kwargs.update({'can_change_price': True})

        return kwargs

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)

        if self.steps.current == '1':
            first_form_data = self.get_cleaned_data_for_step('0')
            facility = first_form_data.get('facility')
            freeSlots = get_free_slots(facility, first_form_data.get('day'))
            freeSlotsIDs = [slot.id for slot in freeSlots]
            allSlots = get_all_slots(facility)
            context.update({'facility': facility, 'allSlots': allSlots, 'freeSlotsIDs': freeSlotsIDs})
        context.update({'isSingleCreateView': True, 'create_res_active': True})
        return context

    def done(self, form_list, **kwargs):
        first_form = form_list[0]
        second_form = form_list[1]

        reservation = first_form.save(commit=False)

        reservation.user = second_form.cleaned_data.get('user')
        reservation.time_slot = second_form.cleaned_data.get('time_slot')

        if self.request.user.has_perm('reservations.change_price'):
            reservation.price = second_form.cleaned_data.get('price')
        else:
            reservation.price = reservation.facility.default_price

        reservation.save()

        return redirect('reservations:home')


class UpdateReservationWizardView(LoginRequiredMixin, PermissionRequiredMixin, SessionWizardView, SingleObjectMixin):
    permission_required = 'reservations.add_reservation'
    model = Reservation
    form_list = [UpdateReservationForm1, UpdateReservationForm2]
    template_name = 'reservationsTemplates/update_reservation.html'

    def get_form_kwargs(self, step=None):
        self.object = self.get_object()
        kwargs = {'old_reservation': self.object}
        if step == '1':
            first_form_data = self.get_cleaned_data_for_step('0')
            new_day = first_form_data.get('day')
            self.newFreeSlots = self.get_new_free_slots(new_day)
            kwargs.update({'freeSlots': self.newFreeSlots})

            if self.request.user.has_perm('reservations.change_price'):
                kwargs.update({'can_change_price': True})

        return kwargs

    def get_new_free_slots(self, new_day):
        freeSlots = get_free_slots(self.object.facility, new_day)
        if (self.object.day == new_day) and (self.object.time_slot is not None):
            oldSlot = TimeSlot.objects.filter(
                pk=self.object.time_slot.id)  # to make it a queryset instead of a model object
            freeSlots |= oldSlot
        return freeSlots

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)

        if self.steps.current == '1':
            allSots = get_all_slots(self.object.facility)
            context.update({'allSlots': allSots, 'freeSlotsIDs': [slot.id for slot in self.newFreeSlots]})

            if self.request.user.has_perm('reservations.change_price'):
                context.update({'can_change_price': True})

        context.update({'oldReservation': self.object, 'res_list_active': True})

        return context

    def done(self, form_list, **kwargs):
        first_form_data = form_list[0].cleaned_data
        second_form_data = form_list[1].cleaned_data

        self.object.day = first_form_data.get('day')
        self.object.time_slot = second_form_data.get('time_slot')

        if self.request.user.has_perm('reservations.change_price'):
            self.object.price = second_form_data.get('price')

        self.object.save()

        return redirect('reservations:reservations-list')


class CreateWeeklyReservationWizardView(LoginRequiredMixin, PermissionRequiredMixin, SessionWizardView):
    permission_required = 'reservations.add_reservation'
    form_list = [WeeklyReservationForm1, WeeklyReservationForm2]
    template_name = 'reservationsTemplates/create_reservation.html'

    def get_form_kwargs(self, step=None):
        if step != '1':
            return {}

        first_form_data = self.get_cleaned_data_for_step('0')
        facility = first_form_data.get('facility')
        day = first_form_data.get('day')
        weeksNumber = first_form_data.get('weeksNumber')

        kwargs = {'fac': facility, 'day': day, 'weeksNumber': weeksNumber}

        if self.request.user.has_perm('reservations.change_price'):
            kwargs.update({'can_change_price': True})
        return kwargs

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)

        if self.steps.current == '1':
            first_form_data = self.get_cleaned_data_for_step('0')
            facility = first_form_data.get('facility')
            freeSlots = get_weekly_free_slots(facility, first_form_data.get('day'), first_form_data.get('weeksNumber'))
            freeSlotsIDs = [slot.id for slot in freeSlots]
            allSlots = get_all_slots(facility)
            context.update({'facility': facility, 'allSlots': allSlots, 'freeSlotsIDs': freeSlotsIDs})
        context.update({'create_res_active': True})
        return context

    def done(self, form_list, **kwargs):
        first_form_data = form_list[0].cleaned_data
        second_form_data = form_list[1].cleaned_data

        if self.request.user.has_perm('reservations.change_price'):
            price = second_form_data.get('price')
        else:
            price = first_form_data.get('facility').default_price

        reservations = createMultipleReservations(first_form_data.get('facility'),
                                                  first_form_data.get('day'),
                                                  second_form_data.get('user'),
                                                  second_form_data.get('time_slot'),
                                                  price,
                                                  first_form_data.get('weeksNumber'))

        redirect_url = reverse_lazy('reservations:reservations-list')
        query_string = urlencode(
            {'user': reservations[0].user.id, 'searchByDay': 'after', 'day': first_form_data.get('day'),
             'facility': reservations[0].facility.id, 'price': second_form_data.get('price')}
        )
        redirect_url = f'{redirect_url}?{query_string}#pagination'

        return redirect(redirect_url)


class ReservationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'reservations.add_reservation'
    model = Reservation
    template_name = 'delete_object.html'
    context_object_name = 'object'
    success_url = reverse_lazy('reservations:home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'res_list_active': True})
        return context
