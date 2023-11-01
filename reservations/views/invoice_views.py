import pytz
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from django.utils import timezone
from django.views import View
from django.http import HttpResponse, Http404

from reservations.models import Reservation

from middleapp.models import Organization


import pdfkit


class GenerateInvoiceView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'reservations.add_reservation'

    def get(self, request, pk):
        try:
            reservation = Reservation.objects.get(id=pk)
            organization = Organization.objects.first()
        except ObjectDoesNotExist:
            raise Http404
        price_before_vat = (reservation.price / 1.15).__round__(2)
        tax = (reservation.price - price_before_vat).__round__(2)
        now = timezone.now().astimezone(pytz.timezone('Asia/Riyadh'))

        logo_url = request.build_absolute_uri(organization.logo.url) if (organization and organization.logo) else ''
        if logo_url.startswith('https://'):
            logo_url = logo_url.replace('https://', 'http://', 1)
        context = {
            'reservation': reservation,
            'organization': organization,
            'invoice_number': f'{reservation.id:04d}',
            'tax': tax,
            'price_before_tax': price_before_vat,
            'now': now.strftime("%H:%M %Y-%m-%d"),
            'logo_url': logo_url,
        }
        html = render_to_string('invoiceTemplates/invoice.html', context)
        pdf = pdfkit.from_string(html, False, options={"enable-local-file-access": ""})

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="فاتورة{reservation.facility}_{reservation.id}.pdf"'
        return response
