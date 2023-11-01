from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from middleapp.forms import OrganizationForm
from middleapp.models import Organization


class OrganizationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Organization
    template_name = 'update_company.html'
    queryset = Organization.objects.filter()
    context_object_name = 'company'
    form_class = OrganizationForm
    success_url = reverse_lazy('users:staff-list')

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'org_active': True})
        return context
