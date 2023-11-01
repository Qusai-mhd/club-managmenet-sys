from django.urls import path
from users.views import *
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('staff-permissions/<int:pk>', EditUserPermissionsView.as_view(), name='edit-permissions'),
    # path('customers', views.CustomersListView.as_view(), name='customer-list'),
    path('', StaffListView.as_view(), name='staff-list'),
    path('create-staff', CreateStaffView.as_view(), name='staff-create'),
    path('create-customer', CreateCustomerView.as_view(), name='customer-create'),
    path('message', PublicMessageView.as_view(), name='message'),
    path('submit-info', CustomerInfoPublicView.as_view(), name='submit-info'),
    path('unconfirmed-customers', UnconfirmedUsersListView.as_view(), name='unconfirmed-customers'),
    path('dismiss-customer/<int:pk>', DismissRequestedCustomer.as_view(), name='dismiss-customer'),
    path('confirm-customer/<int:pk>', AcceptRequestedCustomer.as_view(), name='confirm-customer'),

    path(r'user/<int:pk>/update', StaffUpdateView.as_view(), name='update-user'),
    path(r'user/<int:pk>/delete', StaffDeleteView.as_view(), name='delete-user'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='users:login'), name='logout'),
    path('password-reset/', RequestResetPasswordView.as_view(), name='reset-password'),
    path('password-reset-code/<str:phone>/', EnterCodeView.as_view(), name='enter-code'),
    path('new-password/<str:token>', NewPasswordView.as_view(), name='new-password'),
]
