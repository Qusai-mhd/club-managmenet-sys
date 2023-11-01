from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.views.generic import DetailView, ListView

from middleapp.models import Organization
from subscriptions.models import Invoice, Subscription

import decimal
import pdfkit


class SubscriptionInvoice(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    permission_required = 'subscriptions.add_subscription'
    model = Invoice
    queryset = Invoice.objects.all()

    def get(self, request, *args, **kwargs):
        invoice = self.get_object()
        price_before_vat = (invoice.total_price / decimal.Decimal(1.15)).__round__(2)
        tax = (invoice.total_price - price_before_vat).__round__(2)
        organization = Organization.objects.first()
        logo_url = request.build_absolute_uri(organization.logo.url) if (organization and organization.logo) else ''
        if logo_url.startswith('https://'):
            logo_url = logo_url.replace('https://', 'http://', 1)
        context = {
            'organization': organization,
            'tax': tax,
            'price_before_tax': price_before_vat,
            'invoice': invoice,
            'remaining': invoice.total_price - invoice.paid,
            'logo_url': logo_url,
        }
        html = render_to_string('invoiceTemplates/payment_invoice.html', context)
        pdf = pdfkit.from_string(html, False, options={"enable-local-file-access": ""})

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="فاتورة{invoice.subscription}_{invoice.id}.pdf"'
        return response


class InvoiceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'subscriptions.add_subscription'
    model = Invoice
    template_name = 'invoiceTemplates/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 10

    def get_queryset(self):
        subscription = get_object_or_404(Subscription, pk=self.kwargs.get('pk'))
        return Invoice.objects.filter(subscription=subscription).order_by('-time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subscription = get_object_or_404(Subscription, pk=self.kwargs.get('pk'))
        context['subscription'] = subscription
        context.update({'subs_list_active': True})
        return context
