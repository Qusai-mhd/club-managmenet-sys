from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.db import models
from django.db.models import Count, Subquery, OuterRef
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import CreateView, UpdateView, ListView, DetailView, FormView
from django.views.generic.detail import SingleObjectMixin

from subscriptions.models import SportCategory, Division, TrainingWeekDay, TrainingSessionRecord
from subscriptions.forms import CategoryForm, DivisionForm, get_division_trainingDay_inlineformset_factory
from jsonview.decorators import json_view
from jsonview.exceptions import BadRequest

import pytz


class SportCategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'subscriptions.add_division'
    model = SportCategory
    template_name = 'categoryDivisionWeekDaysTemplates/crate_category.html'
    form_class = CategoryForm
    success_url = reverse_lazy('subscriptions:divisions-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({'subs_divisions_active': True})
        return context


class DivisionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'subscriptions.add_division'
    model = Division
    template_name = 'categoryDivisionWeekDaysTemplates/create_division.html'
    form_class = DivisionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({'subs_divisions_active': True})
        return context

    def get_success_url(self):
        # Use the ID of the created object to construct the success URL
        return reverse_lazy('subscriptions:edit-days', kwargs={'pk': self.object.pk})


class DivisionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'subscriptions.add_division'
    model = Division
    template_name = 'categoryDivisionWeekDaysTemplates/update_object.html'
    queryset = Division.objects.filter()
    context_object_name = 'object'
    form_class = DivisionForm
    success_url = reverse_lazy('subscriptions:divisions-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({'subs_divisions_active': True})
        return context


# An endpoint that receives a division id and returns the division's price
@json_view
def get_division_price(request):
    division_id = request.GET.get('division_id', None)
    if division_id:
        try:
            division_id = float(division_id)
            division = Division.objects.get(id=division_id)
            return {'price': division.default_month_price}
        except Division.DoesNotExist:  # 404
            raise Http404('Division does not exist')
        except (ValueError, TypeError):  # 400
            raise BadRequest('Division id is not a number')

    raise Http404('Division id not provided')


class TodaySessionsListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'subscriptions.add_trainingsessionrecord'
    model = TrainingWeekDay
    template_name = 'categoryDivisionWeekDaysTemplates/today_sessions.html'
    context_object_name = 'sessions'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get the current day of the week as a string (e.g., 'Sunday', 'Monday', etc.)
        current_day_english = timezone.now().astimezone(pytz.timezone('Asia/Riyadh')).strftime('%A')

        # Define current_day_arabic as an instance variable
        self.current_day_arabic = {
            'Sunday': 'الأحد',
            'Monday': 'الاثنين',
            'Tuesday': 'الثلاثاء',
            'Wednesday': 'الأربعاء',
            'Thursday': 'الخميس',
            'Friday': 'الجمعة',
            'Saturday': 'السبت',
        }.get(current_day_english)

    def get_queryset(self):
        today = timezone.now().astimezone(pytz.timezone('Asia/Riyadh')).date()
        # Subquery to get existing records today
        existing_records_today = TrainingSessionRecord.objects.filter(date=today)

        # Query to exclude WeakDays that already have a TrainingSessionRecord for today
        queryset = (TrainingWeekDay.objects.filter(division__suspended=False).annotate(
            existing_records_today=Subquery(
                existing_records_today.filter(division=OuterRef('division_id')).values('id'),
                output_field=models.IntegerField()))
                    .filter(day=self.current_day_arabic)
                    .annotate(subscription_count=Count('division__subscriptions'))
                    .order_by('start_time'))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        sessions_count=self.get_queryset().count()
        context.update({'subs_today_sessions_active': True, 'sessions_count':sessions_count})
        return context


class DivisionsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Division
    template_name = 'categoryDivisionWeekDaysTemplates/divisions.html'
    context_object_name = 'divisions'
    queryset = Division.objects.all().annotate(subscription_count=Count('subscriptions'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({'subs_divisions_active': True})
        return context

    def test_func(self):
        return (self.request.user.has_perm('subscriptions.add_division') or
                self.request.user.has_perm('subscriptions.add_trainingweekday'))


class DivisionDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Division
    template_name = 'categoryDivisionWeekDaysTemplates/get_division.html'
    context_object_name = 'division'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({'subs_divisions_active': True})
        return context

    def test_func(self):
        return (self.request.user.has_perm('subscriptions.add_division') or
                self.request.user.has_perm('subscriptions.add_trainingweekday'))


class TrainingDaysEditView(LoginRequiredMixin, PermissionRequiredMixin, SingleObjectMixin, FormView):
    permission_required = 'subscriptions.add_trainingweekday'
    model = Division
    template_name = 'categoryDivisionWeekDaysTemplates/division_training_days_edit.html'

    @property
    def extras(self):
        TOTAL_FORMS = 7
        days_number = self.object.training_days.count()
        return TOTAL_FORMS - days_number

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=Division.objects.filter(pk=kwargs.get('pk')))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=Division.objects.filter(pk=kwargs.get('pk')))
        return super().post(request, *args, **kwargs)

    def get_form(self, form_class=None):
        return get_division_trainingDay_inlineformset_factory(extra=self.extras)(**self.get_form_kwargs(),
                                                                                 instance=self.object)

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('subscriptions:get-division', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'subs_divisions_active': True})
        return context
