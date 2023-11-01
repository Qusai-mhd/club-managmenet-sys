from django.urls import path

from .views import *

urlpatterns = [
    path('', TodaySessionsListView.as_view(), name='home'),

    path('createCategory', SportCategoryCreateView.as_view(), name='create-category'),

    path('divisions', DivisionsListView.as_view(), name='divisions-list'),
    path('createDivision', DivisionCreateView.as_view(), name='create-division'),
    path(r'division/<int:pk>', DivisionDetailView.as_view(), name='get-division'),
    path(r'division/<int:pk>/update', DivisionUpdateView.as_view(), name='update-division'),

    path('create-subscription', SubscriptionCreateView.as_view(), name='create-subscription'),
    path('get-division-price', get_division_price, name='get-division-price'),
    path('extend-subscription/<int:pk>', SubscriptionExtendView.as_view(), name='extend-subscription'),
    path('make-payment/<int:pk>', SubscriptionPaymentView.as_view(), name='make-payment'),
    path('search-subscriptions', SubscriptionListFormView.as_view(), name='search-subscriptions'),
    path('subscription-detail/<int:pk>',SubscriptionDetailView.as_view(), name='subscription-detail'),
    path('delete-subscription/<int:pk>', DeleteSubscriptionView.as_view(), name='delete-subscription'),

    path('edit-days/<int:pk>', TrainingDaysEditView.as_view(), name='edit-days'),

    path('training-attendance/<int:pk>', CreateTrainingAttendanceView.as_view(), name='training-attendance'),
    path('update-attendance/<int:pk>', UpdateTrainingAttendanceView.as_view(), name='update-attendance'),
    path('previous-records', PreviousRecordsList.as_view(), name='previous-records'),
    path('attendance-records/<int:pk>', AttendanceRecordsView.as_view(), name='attendance-records'),
    path('attendance-history/<int:pk>', IndividualHistoryList.as_view(), name='individual-history'),

    path('summaryreport', SummaryReportView.as_view(), name='summary-report'),
    path('choosereport', ChooseReportView.as_view(), name='choose-report'),

    path('invoice/<int:pk>', SubscriptionInvoice.as_view(), name='invoice'),
    path('invoice-list/<int:pk>', InvoiceListView.as_view(), name='invoice-list'),
]
