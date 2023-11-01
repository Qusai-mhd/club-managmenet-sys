from urllib.parse import urlencode

from django.shortcuts import redirect, get_object_or_404
from django.core import signing
from django.http import HttpResponseForbidden, Http404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView, UpdateView, FormView, TemplateView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib import messages

from users.forms import StaffCreateForm, CustomerCreateForm, StaffPermissionsForm, LoginForm, PhoneForm, CodeForm, \
    NewPasswordForm, StaffUpdateForm, CustomerInfoPublicForm, CustomerConfirmationForm
from users.models import RSUser
from users.authentication import send_whatsapp_code, check_code
from twilio.base.exceptions import TwilioRestException

from users.utilities import get_url_for_permission


class UsersListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    # For inheritance only, not to be used as a view
    model = RSUser
    context_object_name = 'users'


# must be linked up with a new table refere to the reservations customers to distingues between reservations
# and subscribers users.
# class CustomersListView(UsersListView):
#     queryset = RSUser.objects.filter(is_staff=False, is_superuser=False)
#     template_name = 'customers.html'
#
#      this view should extend from base file of the reservations app
#
# def test_func(self):
#     return self.request.user.is_staff


class StaffListView(UsersListView):
    queryset = RSUser.objects.filter(is_staff=True)
    template_name = 'staff_list.html'

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'staff_list_active': True})
        return context


class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    # For inheritance only, not to be used as a view
    model = RSUser
    template_name = 'create_user.html'

    def test_func(self):
        return self.request.user.is_superuser


class CreateCustomerView(UserCreateView):
    form_class = CustomerCreateForm

    def form_valid(self, form):
        customer = form.save(commit=False)
        customer.is_staff = False
        customer.confirmed = True
        customer.save()
        return super().form_valid(form)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'title': 'إنشاء حساب عميل'})
        return context

    def test_func(self):
        return self.request.user.is_staff

    def get_success_url(self):
        if self.request.user.has_perm('reservations.add_reservation'):
            return reverse_lazy('reservations:home')
        elif self.request.user.has_perm('subscriptions.add_subscription'):
            return reverse_lazy('subscriptions:search-subscriptions')


class PublicMessageView(TemplateView):
    template_name = 'public_message.html'


class CustomerInfoPublicView(CreateView):
    model = RSUser
    template_name = 'submit_info.html'
    form_class = CustomerInfoPublicForm
    success_url = reverse_lazy('users:message')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.confirmed = False
        user.is_staff = False
        user.save()
        messages.success(self.request, 'تم إرسال معلوماتك بنجاح، سيتم التواصل معكم قريباً')
        return super().form_valid(form)


class UnconfirmedUsersListView(LoginRequiredMixin,UserPassesTestMixin, ListView):
    model = RSUser
    template_name = 'unconfirmed_customers.html'
    paginate_by = 10

    def get_queryset(self):
        return RSUser.objects.filter(confirmed=False)

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'customer_unconfirmed_active': True})
        return context


class DismissRequestedCustomer(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = RSUser
    queryset = RSUser.objects.filter(confirmed=False)
    success_url = reverse_lazy('users:unconfirmed-customers')
    template_name = 'dismiss_customer.html'
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({'customer_unconfirmed_active': True})
        return context

    def test_func(self):
        return self.request.user.is_staff


class AcceptRequestedCustomer(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'accept_customer.html'
    form_class = CustomerConfirmationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = get_object_or_404(RSUser, pk=self.kwargs['pk'], confirmed=False)
        context.update({'customer': customer, 'customer_unconfirmed_active': True})
        return context

    def form_valid(self, form):
        self.customer = get_object_or_404(RSUser, pk=self.kwargs['pk'], confirmed=False)
        confirmed = form.cleaned_data['confirm_button']
        if confirmed:
            self.customer.confirmed = True
            self.customer.save()
        return super().form_valid(form)

    def get_success_url(self):
        redirect_url = reverse_lazy('subscriptions:create-subscription')
        customer_id = self.customer.id
        query_string = urlencode({'user': customer_id})
        redirect_url = f'{redirect_url}?{query_string}'
        return redirect_url

    def test_func(self):
        return self.request.user.is_staff


class CreateStaffView(UserCreateView):
    form_class = StaffCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'title': 'إنشاء حساب موظف', 'create_staff_active': True})
        return context

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_staff = True
        user.save()

        self.success_url = reverse_lazy('users:edit-permissions', kwargs={'pk': user.pk})

        return super().form_valid(form)

    def test_func(self):
        return self.request.user.is_superuser


class EditUserPermissionsView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = RSUser
    queryset = RSUser.objects.filter(is_staff=True)
    form_class = StaffPermissionsForm
    template_name = 'edit_permissions.html'
    success_url = reverse_lazy('users:staff-list')
    context_object_name = 'user_to_edit'

    def form_valid(self, form):
        user = form.save(commit=False)
        formData = form.cleaned_data
        reservations_permissions = formData.get('reservations_permissions_field')
        subscriptions_permissions = formData.get('subscriptions_permissions_field')
        user.user_permissions.set(reservations_permissions | subscriptions_permissions)
        user.save()

        return super().form_valid(form)

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'create_staff_active': True})
        return context


class StaffUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = RSUser
    template_name = 'update_user.html'
    queryset = RSUser.objects.filter(is_staff=True)
    context_object_name = 'user_to_edit'
    form_class = StaffUpdateForm
    success_url = reverse_lazy('users:staff-list')

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'staff_list_active': True})
        return context


class StaffDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = RSUser
    template_name = 'delete_user.html'
    queryset = RSUser.objects.filter(is_staff=True)
    context_object_name = 'user_to_delete'
    success_url = reverse_lazy('users:staff-list')

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'staff_list_active': True})
        return context


class CustomLoginView(LoginView):
    redirect_authenticated_user = True
    form_class = LoginForm

    def form_valid(self, form):
        # Login only if the user is a staff member or a superuser
        user = form.get_user()
        if user.is_superuser or user.is_staff:
            url_for_permissions = get_url_for_permission(user)
            if url_for_permissions:
                return super().form_valid(form)
            else:
                return HttpResponseForbidden()

        messages.error(self.request, 'رقم الهاتف أو كلمة المرور غير صحيحة')
        return redirect('users:login')

    def get_success_url(self):
        user = self.request.user
        return get_url_for_permission(user)


class RequestResetPasswordView(FormView):
    template_name = 'registration/reset_password.html'
    form_class = PhoneForm

    def form_valid(self, form):
        phone = form.cleaned_data['phone']

        user = RSUser.objects.get(phone=phone)
        if (not user) or not (user.is_staff or user.is_superuser):
            return redirect('users:login')

        check = send_whatsapp_code(phone)
        if not check:
            messages.error(self.request, 'حدث خطأ أثناء إرسال الرمز، حاول مرة أخرى')
            redirect('users:reset-password')

        return redirect('users:enter-code', phone=phone)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'title': 'إعادة تعيين كلمة المرور', 'heading': 'إعادة تعيين كلمة المرور', 'sub': 'أرسل الرمز'})
        return context


class EnterCodeView(FormView):
    form_class = CodeForm
    template_name = 'registration/reset_password.html'

    def get_initial(self):
        return {'phone': self.kwargs.get('phone')}

    def form_valid(self, form):
        phone = form.cleaned_data['phone']
        code = form.cleaned_data['code']

        user = RSUser.objects.get(phone=phone)
        if (not user) or not (user.is_staff or user.is_superuser):
            messages.error(self.request, 'رقم الهاتف غير صحيح')
            return redirect('users:login')

        try:
            verification_check = check_code(phone, code)
        except TwilioRestException:
            raise Http404

        if not verification_check:
            messages.error(self.request, 'الرمز غير صحيح')
            return redirect('users:enter-code', phone=phone)

        token = signing.dumps({'phone': phone})

        return redirect('users:new-password', token=token)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {'title': 'إعادة تعيين كلمة المرور', 'heading': 'أدخل الرمز المرسل إلى واتساب', 'sub': 'أدخل الرمز'})
        return context


class NewPasswordView(FormView):
    form_class = NewPasswordForm
    template_name = 'registration/reset_password.html'

    def get(self, request, *args, **kwargs):

        token = self.kwargs.get('token')
        if not token:
            return redirect('users:reset-password')
        try:
            signing.loads(token, max_age=300)['phone']
        except signing.SignatureExpired:
            messages.error(self.request, 'انتهت صلاحية الرمز')
            return redirect('users:reset-password')
        except signing.BadSignature:
            return redirect('users:login')

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):

        token = self.kwargs.get('token')
        if not token:
            return redirect('users:reset-password')
        try:
            phone = signing.loads(token, max_age=300)['phone']
        except signing.SignatureExpired:
            messages.error(self.request, 'انتهت صلاحية الرمز')
            return redirect('users:reset-password')
        except signing.BadSignature:
            return redirect('users:login')

        user = RSUser.objects.get(phone=phone)
        password = form.cleaned_data['password1']
        password2 = form.cleaned_data['password2']

        if password != password2:
            messages.error(self.request, 'كلمتا المرور غير متطابقتين')
            return redirect('users:new-password', token=token)

        user.set_password(password)
        user.save()

        messages.success(self.request, 'تم تغيير كلمة المرور بنجاح')
        return redirect('users:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'title': 'إعادة تعيين كلمة المرور', 'heading': 'أدخل كلمة المرور الجديدة', 'sub': 'أدخل كلمة المرور'})
        return context
