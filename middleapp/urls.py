from django.urls import path

from middleapp.views import OrganizationUpdateView

urlpatterns = [
    path('company/<int:pk>', OrganizationUpdateView.as_view(), name='update-company'),
]
