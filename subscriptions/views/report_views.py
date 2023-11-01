from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.views import View
from django.views.generic import FormView
from django.http import HttpResponse
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages

from urllib.parse import urlencode
from datetime import datetime
import pdfkit
import calendar
import pytz

from subscriptions.forms import SubscriptionsReportForm
from subscriptions.queries import get_summary_report


class ChooseReportView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    permission_required = ''

    form_class = SubscriptionsReportForm
    template_name = 'reports/choose_report_super.html'

    def get_initial(self):
        now = timezone.now().astimezone(pytz.timezone('Asia/Riyadh'))
        this_month = now.month
        this_year = now.year

        return {'month': this_month, 'year': this_year}

    def form_valid(self, form):
        report_period = form.cleaned_data.get('reportPeriod')

        if report_period == 'monthly':
            if not form.cleaned_data.get('month') or not form.cleaned_data.get('year'):
                messages.error(self.request, 'يجب اختيار الشهر والسنة')
                return redirect('subscriptions:choose-report')

            month = int(form.cleaned_data.get('month'))
            year = form.cleaned_data.get('year')

            try:
                month = int(month)
                year = int(year)
            except (ValueError, TypeError):
                messages.error(self.request, "قيمة الشهر أو السنة غير صحيحة")
                return redirect('subscriptions:choose-report')

            _, end_day = calendar.monthrange(year, month)

            start_date = datetime(year=int(year), month=int(month), day=1).astimezone(pytz.timezone('Asia/Riyadh'))
            end_date = datetime(year=int(year), month=int(month), day=end_day).astimezone(pytz.timezone('Asia/Riyadh'))

        elif report_period == 'yearly':
            if not form.cleaned_data.get('year'):
                messages.error(self.request, 'يجب اختيار السنة')
                return redirect('subscriptions:choose-report')

            year = form.cleaned_data.get('year')
            start_date = datetime(year=int(year), month=1, day=1).astimezone(pytz.timezone('Asia/Riyadh'))
            end_date = datetime(year=int(year), month=12, day=31).astimezone(pytz.timezone('Asia/Riyadh'))

        else:  # custom
            if not form.cleaned_data.get('dayFrom') or not form.cleaned_data.get('dayTo'):
                messages.error(self.request, 'يجب اختيار تاريخ البداية والنهاية')
                return redirect('subscriptions:choose-report')

            start_date = form.cleaned_data.get('dayFrom')
            end_date = form.cleaned_data.get('dayTo')

        # format the dates to be %Y-%m-%d
        start_date = start_date.strftime('%Y-%m-%d')
        end_date = end_date.strftime('%Y-%m-%d')

        # if report_type == 'summary':
            # redirect to summary report with get parameters

        redirect_url = reverse('subscriptions:summary-report')
        query_string = urlencode({'start_date': start_date, 'end_date': end_date})
        redirect_url = f'{redirect_url}?{query_string}'

        return redirect(redirect_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({'subs_report_active': True})
        return context


class SummaryReportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = ''

    options = {
        'page-size': 'Letter',
        'margin-top': '0.5in',
        'margin-right': '0.5in',
        'margin-bottom': '0.5in',
        'margin-left': '0.5in',
    }

    def get(self, request):
        if self.request.method == 'GET':

            # get the start_date and end_date from the URL keyword arguments
            start_date = self.request.GET.get('start_date')
            end_date = self.request.GET.get('end_date')
            if not start_date or not end_date:
                messages.error(self.request, 'يجب اختيار تاريخ التقرير بشكل صحيح')
                return redirect('subscriptions:choose-report')

            # validate the date types
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').astimezone(pytz.timezone('Asia/Riyadh'))
                end_date = datetime.strptime(end_date, '%Y-%m-%d').astimezone(pytz.timezone('Asia/Riyadh'))
            except (ValueError, TypeError):
                messages.error(self.request, "يجب اختيار تاريخ التقرير بشكل صحيح")
                return redirect('subscriptions:choose-report')

            reports = get_summary_report(start_date, end_date)

            time = timezone.now().astimezone(pytz.timezone('Asia/Riyadh')).strftime("%Y-%m-%d %H:%M")

            context = {
                'reports': reports,
                'time': time,
                'start_date': start_date,
                'end_date': end_date,
            }
            html = render_to_string('reports/summary_report.html', context)

            pdf = pdfkit.from_string(html, False, options=self.options)

            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="Subscriptions_Summary_Report_{time}.pdf"'
            return response
