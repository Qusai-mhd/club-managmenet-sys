from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, DetailView, UpdateView, FormView
from django.views.generic.detail import SingleObjectMixin

from reservations.forms import get_FTS_inlineformset_factory, FacilityForm, CategoryForm
from reservations.models import Facility, FacilityCategory, TimeSlot

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin

from reservations.utilities import check_time_conflict


class FacilitiesListView(LoginRequiredMixin,UserPassesTestMixin, ListView):
    model = Facility
    template_name = 'CategoryFacilityTemplates/facilities.html'
    queryset = Facility.objects.filter()
    context_object_name = 'facilities'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'facilities_active': True})
        return context

    def test_func(self):
        return (self.request.user.has_perm('reservations.add_facility') or
                self.request.user.has_perm('reservations.add_timeslot'))


class FacilityCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'reservations.add_facility'
    model = Facility
    template_name = 'CategoryFacilityTemplates/create_facility.html'
    form_class = FacilityForm

    def get_success_url(self):
        # Use the ID of the created object to construct the success URL
        return reverse_lazy('reservations:facility-timeslot-edit', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'facilities_active': True})
        return context


class FacilityDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Facility
    template_name = 'CategoryFacilityTemplates/get_facility.html'
    context_object_name = 'facility'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'facilities_active': True})
        return context

    def test_func(self):
        return (self.request.user.has_perm('reservations.add_facility') or
                self.request.user.has_perm('reservations.add_timeslot'))


class FacilityUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'reservations.add_facility'
    model = Facility
    template_name = 'CategoryFacilityTemplates/update_object.html'
    queryset = Facility.objects.filter()
    context_object_name = 'object'
    form_class = FacilityForm
    success_url = reverse_lazy('reservations:facilities-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'facilities_active': True})
        return context


# class FacilityDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
#     permission_required = 'reservations.add_facility'
#     model = Facility
#     template_name = 'delete_object.html'
#     queryset = Facility.objects.filter()
#     context_object_name = 'object'
#     success_url = reverse_lazy('reservations:facilities-list')


class CategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'reservations.add_facility'
    model = FacilityCategory
    template_name = 'CategoryFacilityTemplates/create_category.html'
    form_class = CategoryForm
    success_url = reverse_lazy('reservations:facilities-list')


class TimeSlotEditView(LoginRequiredMixin, PermissionRequiredMixin, SingleObjectMixin, FormView):
    permission_required = 'reservations.add_timeslot'
    model = Facility
    template_name = 'CategoryFacilityTemplates/facility_timeslot_edit.html'

    @property
    def extras(self):
        TOTAL_FORMS = 15
        TS_number = self.object.timeslot_set.count()
        return TOTAL_FORMS - TS_number

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=Facility.objects.filter(pk=kwargs.get('pk')))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=Facility.objects.filter(pk=kwargs.get('pk')))
        return super().post(request, *args, **kwargs)

    def get_form(self, form_class=None):
        return get_FTS_inlineformset_factory(extra=self.extras)(**self.get_form_kwargs(), instance=self.object)

    def form_valid(self, form):
        changedSlots = form.save(commit=False)
        unchangedSlots = TimeSlot.objects.filter(facility=self.object).exclude(pk__in=[obj.pk for obj in changedSlots])
        allSlots = list(changedSlots) + list(unchangedSlots)

        for changed in changedSlots:
            other_slots = [slot for slot in allSlots if slot != changed]
            for other in other_slots:
                if check_time_conflict(changed, other):
                    messages.error(self.request, 'هناك تعارض بين الفترات الزمنية')
                    return self.form_invalid(form)

        form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('reservations:get-facility', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'facilities_active': True})
        return context

