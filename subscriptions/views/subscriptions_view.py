from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, UpdateView, ListView, DetailView
from django.views.generic.edit import FormMixin, DeleteView

from subscriptions.models import Subscription, SubscriptionPeriod, Invoice
from subscriptions.forms import SubscriptionCreateForm, ExtendSubscriptionForm, SubscriptionPaymentForm, \
    SubscriptionSearchForm
from subscriptions.utilities import add_months, get_confirmed_subscription_queryset_from_params, \
    validate_subscription_search_params

import pytz


class SubscriptionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'subscriptions.add_subscription'
    model = Subscription
    template_name = 'subsTemplates/create_subscription.html'
    form_class = SubscriptionCreateForm

    def get_initial(self):
        initial = super().get_initial()
        user = self.request.GET.get('user', None)
        if user:
            try:
                user = get_user_model().objects.get(id=int(user), confirmed=True, is_staff=False)
                initial.update({'user': user.id})
            except (ValueError, TypeError, get_user_model().DoesNotExist):
                pass  # Pass silently if the user does not exist or the id is invalid
        initial.update({'start_date': timezone.now().astimezone(pytz.timezone('Asia/Riyadh')).date()})
        return initial

    def form_valid(self, form):
        user = form.cleaned_data['user']
        division = form.cleaned_data['division']

        # if there is a subscription already registered, return an error
        existing = Subscription.objects.filter(user=user, division=division)
        if existing.exists():
            form.add_error('division',
                           'المشترك مسجل مسبقا في هذه الفئة!')
            return self.form_invalid(form)
        new_sub = form.save(commit=False)
        new_sub.user = form.cleaned_data['user']
        new_sub.division = form.cleaned_data['division']
        new_sub.save()
        self.object = new_sub
        start_date = form.cleaned_data['start_date']
        end_date = add_months(start_date, form.cleaned_data['months_num'])

        if self.request.user.has_perm('subscriptions.change_subs_price'):
            price = form.cleaned_data['price']
        else:
            price = form.cleaned_data['division'].default_month_price

        paid_amount = form.cleaned_data['initial_paid_amount']
        if paid_amount > (price * form.cleaned_data['months_num']):
            form.add_error('initial_paid_amount',
                           'المبلغ المدفوع أكبر من المبلغ المستحق!')
            new_sub.delete()
            return self.form_invalid(form)

        period = SubscriptionPeriod.objects.create(
            subscription=new_sub,
            start_date=start_date,
            end_date=end_date,
            price=price * form.cleaned_data['months_num'],
            paid_amount=paid_amount,
        )
        period.save()

        if form.cleaned_data['initial_paid_amount'] != 0:
            invoice = Invoice.objects.create(
                subscription=new_sub,
                total_price=price * form.cleaned_data['months_num'],
                paid=form.cleaned_data['initial_paid_amount'],
                time=timezone.now().astimezone(pytz.timezone('Asia/Riyadh')),
                action='اشتراك جديد'
            )
            invoice.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['enable_price_field'] = self.request.user.has_perm('subscriptions.change_subs_price')
        return kwargs

    def get_success_url(self):
        return reverse_lazy('subscriptions:subscription-detail', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({'subs_create_active': True})
        return context


class SubscriptionExtendView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'subscriptions.add_subscription'
    model = Subscription
    template_name = 'subsTemplates/extend_subscription.html'
    form_class = ExtendSubscriptionForm
    context_object_name = 'subscription'

    def get(self, request, *args, **kwargs):
        # validate that the division is not suspended
        if self.get_object().division.suspended:
            messages.error(self.request, 'لا يمكن تمديد الاشتراك لأن الفئة موقوفة!')
            return redirect('subscriptions:subscription-detail', pk=self.get_object().id)

        return super().get(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        most_recent_period_end = self.object.most_recent_period.end_date
        today = timezone.now().astimezone(pytz.timezone('Asia/Riyadh')).date()

        # If the subscription has expired, set the start date to today.
        # Otherwise, set it to the end date of the subscription's most recent period.
        start_date = most_recent_period_end if most_recent_period_end > today else today
        initial.update({'start_date': start_date, 'price': self.object.division.default_month_price,
                        'total_price': self.object.division.default_month_price})
        return initial

    def form_valid(self, form):

        if self.get_object().division.suspended:
            messages.error(self.request, 'لا يمكن تمديد الاشتراك لأن الفئة موقوفة!')
            return redirect('subscriptions:subscription-detail', pk=self.get_object().id)

        start_date = form.cleaned_data['start_date']
        end_date = add_months(start_date, form.cleaned_data['months_num'])

        if self.request.user.has_perm('subscriptions.change_subs_price'):
            price = form.cleaned_data['price']
        else:
            price = self.get_object().division.default_month_price

        paid_amount = form.cleaned_data['initial_paid_amount']

        if paid_amount > (price * form.cleaned_data['months_num']):
            form.add_error('initial_paid_amount',
                           'المبلغ المدفوع أكبر من المبلغ المستحق!')
            return self.form_invalid(form)

        if start_date < self.object.most_recent_period.end_date:
            form.add_error('start_date',
                           'تاريخ البدء يجب أن يكون بعد تاريخ انتهاء الفترة الحالية!')
            return self.form_invalid(form)

        period = SubscriptionPeriod.objects.create(
            subscription=self.object,
            start_date=start_date,
            end_date=end_date,
            price=price * form.cleaned_data['months_num'],
            paid_amount=paid_amount,
        )
        period.save()

        if paid_amount != 0:
            invoice = Invoice.objects.create(
                subscription=self.object,
                total_price=price * form.cleaned_data['months_num'],
                paid=paid_amount,
                time=timezone.now().astimezone(pytz.timezone('Asia/Riyadh')),
                action='تمديد اشتراك'
            )
            invoice.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subscription_end_date = self.object.most_recent_period.end_date.strftime('%d/%m/%Y')

        context.update({'subscription_end_date': subscription_end_date, 'subs_list_active': True})
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['enable_price_field'] = self.request.user.has_perm('subscriptions.change_subs_price')
        return kwargs

    def get_success_url(self):
        return reverse_lazy('subscriptions:subscription-detail', kwargs={'pk': self.object.id})


class SubscriptionPaymentView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'subscriptions.add_subscription'
    model = Subscription
    template_name = 'subsTemplates/subscription_payment.html'
    form_class = SubscriptionPaymentForm

    def get(self, request, *args, **kwargs):
        if self.get_object().total_due_payment_property <= 0:
            messages.error(self.request, 'لا يوجد مبلغ مستحق!')
            return redirect('subscriptions:subscription-detail', pk=self.get_object().id)
        return super().get(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial.update({'due_amount': self.object.total_due_payment_property})
        return initial

    def form_valid(self, form):
        subscription = self.object
        total_due = subscription.total_due_payment_property
        if total_due <= 0:
            messages.error(self.request, 'لا يوجد مبلغ مستحق!')
            return redirect('subscriptions:subscription-detail', pk=self.get_object().id)
        elif form.cleaned_data['new_payment'] > total_due:
            form.add_error('new_payment',
                           'المبلغ المدفوع أكبر من المبلغ المستحق!')
            return self.form_invalid(form)
        subscription.make_payment(form.cleaned_data['new_payment'])
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'subscription': self.object, 'subs_list_active': True})
        return context

    def get_success_url(self):
        return reverse_lazy('subscriptions:subscription-detail', kwargs={'pk': self.object.id})


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


class SubscriptionListFormView(LoginRequiredMixin, UserPassesTestMixin, FormListView):
    form_class = SubscriptionSearchForm
    model = Subscription
    template_name = 'subsTemplates/subscriptions_list_form.html'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.GET
        return get_confirmed_subscription_queryset_from_params(queryset, params)

    def get_initial(self):
        params = self.request.GET
        params = validate_subscription_search_params(params)

        return params

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.now().astimezone(pytz.timezone('Asia/Riyadh')).date()
        after_three_days = today + timezone.timedelta(days=3)

        context.update({'today': today, 'after_three_days': after_three_days, 'subs_list_active': True})

        return context

    def test_func(self):
        return (self.request.user.has_perm('subscriptions.add_subscription') or
                self.request.user.has_perm('subscriptions.view_subscription'))


class SubscriptionDetailView(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    permission_required = 'subscriptions.add_subscription'
    model = Subscription
    template_name = 'subsTemplates/subscription_detail.html'
    context_object_name = 'subscription'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({'subs_list_active': True})
        return context


class DeleteSubscriptionView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'subscriptions.add_subscription'
    model = Subscription
    template_name = 'subsTemplates/delete_subscription.html'
    success_url = reverse_lazy('subscriptions:search-subscriptions')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({'subs_list_active': True, 'subscription': self.object})
        return context
