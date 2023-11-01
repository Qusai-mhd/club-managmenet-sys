from django.urls import path

from .views import *

urlpatterns = [
    path('facilities', FacilitiesListView.as_view(), name='facilities-list'),
    path('createfacility', FacilityCreateView.as_view(), name='create-facility'),
    path(r'facility/<int:pk>', FacilityDetailView.as_view(), name='get-facility'),
    path(r'facility/<int:pk>/update', FacilityUpdateView.as_view(), name='update-facility'),
    # path(r'facility/<int:pk>/delete', FacilityDeleteView.as_view(), name='delete-facility'),
    path('facility/<int:pk>/timeslots/edit/', TimeSlotEditView.as_view(), name='facility-timeslot-edit'),

    path('createCategory', CategoryCreateView.as_view(), name='create-category'),

    path('', ReservationsListView.as_view(), name='home'),
    path('reservations', ReservationListFormView.as_view(), name='reservations-list'),
    path('createreservation', ReservationWizardView.as_view(), name='create-reservation'),
    path('updateReservation/<int:pk>', UpdateReservationWizardView.as_view(), name='update-reservation'),
    path('deleteReservation/<int:pk>', ReservationDeleteView.as_view(), name='delete-reservation'),
    path('createweeklyreservation', CreateWeeklyReservationWizardView.as_view(), name='create-weekly-reservation'),

    path('freeslots/<str:day>', FreeSlotsView.as_view(), name='free-slots'),

    path('summaryreport', SummaryReportView.as_view(), name='summary-report'),
    path('recordsReport', ReservationsRecordsView.as_view(), name='records-report'),
    path('choosereport', ChooseReportView.as_view(), name='choose-report'),
    path('choosereportstaff', ChooseReportViewStaff.as_view(), name='choose-report-staff'),

    path('invoice/<int:pk>', GenerateInvoiceView.as_view(), name='generate-invoice'),


]
