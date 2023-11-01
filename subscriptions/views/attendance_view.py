import pdfkit
import pytz
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.db import models
from django.db.models import Subquery, OuterRef, Count, Q
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView
from django.views.generic.edit import FormView
from django.views import View
from django.core.exceptions import ObjectDoesNotExist

from subscriptions.models import TrainingSessionRecord, IndividualAttendanceRecord, TrainingWeekDay, \
    SubscriptionPeriod, Subscription
from subscriptions.forms import AttendanceForm, UpdateAttendanceForm


class CreateTrainingAttendanceView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    permission_required = 'subscriptions.add_trainingsessionrecord'
    template_name = 'attendance/attendance_record.html'
    form_class = AttendanceForm
    success_url = reverse_lazy('subscriptions:home')

    def get(self, request, *args, **kwargs):
        now = timezone.now().astimezone(pytz.timezone('Asia/Riyadh'))
        today = now.strftime('%A')

        today_arabic = {
            'Sunday': 'الأحد',
            'Monday': 'الاثنين',
            'Tuesday': 'الثلاثاء',
            'Wednesday': 'الأربعاء',
            'Thursday': 'الخميس',
            'Friday': 'الجمعة',
            'Saturday': 'السبت',
        }.get(today)

        # validate that today is a training day for the division
        self.training_day = get_object_or_404(TrainingWeekDay, pk=self.kwargs['pk'])
        if today_arabic != self.training_day.day:
            messages.error(request, f'اليوم ليس {self.training_day.day}')
            return redirect('subscriptions:home')

        # validate if the division is suspended
        if self.training_day.division.suspended:
            messages.error(request, f'التدريبات لفئة {self.training_day.division} متوقفة حالياً')
            return redirect('subscriptions:home')

        # validate that there is no existing record for today
        training_session_record = TrainingSessionRecord.objects.filter(division=self.training_day.division,
                                                                       date=now.date())
        if training_session_record.exists():
            messages.error(request, f'تم تسجيل حضور اليوم بالفعل، بإمكانك تعديل السجل.')
            return redirect('subscriptions:home')

        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if not hasattr(self, 'training_day'):
            self.training_day = get_object_or_404(TrainingWeekDay, pk=self.kwargs['pk'])

        subscriptions = self.training_day.division.subscriptions.all()

        # Send the names of the students to the form kwargs to create the fields dynamically
        form_fields = []
        for subscription in subscriptions:
            field_name = f'student_{subscription.user.id}'
            field_label = f'{subscription.user.full_name}'
            form_fields.append((field_name, field_label))
        kwargs['custom_form_fields'] = form_fields
        return kwargs

    def form_valid(self, form):
        cleaned_data = form.cleaned_data
        if not hasattr(self, 'training_day'):
            self.training_day = get_object_or_404(TrainingWeekDay, pk=self.kwargs['pk'], division__suspended=False)

        today = timezone.now().astimezone(pytz.timezone('Asia/Riyadh')).date()

        # validate that there is no existing record for today
        existing_training_session_record = TrainingSessionRecord.objects.filter(division=self.training_day.division,
                                                                                date=today)
        if existing_training_session_record.exists():
            messages.error(self.request, f'تم تسجيل حضور اليوم بالفعل، بإمكانك تعديل السجل.')
            return redirect('subscriptions:home')

        trainingSessionRecord = TrainingSessionRecord.objects.create(division=self.training_day.division, date=today)
        trainingSessionRecord.save()
        for field_name, attended in cleaned_data.items():
            if field_name.startswith('student_'):
                student_id = field_name.split('_')[1]
                try:
                    student = get_user_model().objects.get(pk=student_id)
                except get_user_model().DoesNotExist:
                    trainingSessionRecord.delete()
                    messages.error(self.request, f'حدث خطأ ما أثناء تسجيل الحضور. الرجاء المحاولة مرة أخرى')
                    return redirect('subscriptions:home')

                individualAttendanceRecord = (IndividualAttendanceRecord.objects
                                              .create(user=student, training_session_record=trainingSessionRecord,
                                                      attended=attended))
                individualAttendanceRecord.save()

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not hasattr(self, 'training_day'):
            self.training_day = get_object_or_404(TrainingWeekDay, pk=self.kwargs['pk'], division__suspended=False)
        today = timezone.now().astimezone(pytz.timezone('Asia/Riyadh')).date()

        # Get the subscriptions for the division, annotated with the end_date,
        # so the expired subscriptions are can be highlighted
        subscriptions = self.training_day.division.subscriptions.annotate(
            latest_end_date=Subquery(
                SubscriptionPeriod.objects.filter(
                    subscription=OuterRef('pk')
                ).order_by('-end_date').values('end_date')[:1]
            )
        ).order_by('-latest_end_date')

        after_three_days = today + timezone.timedelta(days=3)

        context.update({'division': self.training_day.division, 'today': today, 'subscriptions': subscriptions,
                        'after_three_days': after_three_days, 'subs_today_sessions_active': True})
        return context


class UpdateTrainingAttendanceView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    permission_required = 'subscriptions.add_trainingsessionrecord'
    template_name = 'attendance/attendance_record.html'
    form_class = UpdateAttendanceForm
    success_url = reverse_lazy('subscriptions:home')

    def get(self, request, *args, **kwargs):
        self.training_session_record = get_object_or_404(TrainingSessionRecord, pk=self.kwargs['pk'])
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if not hasattr(self, 'training_session_record'):
            self.training_session_record = get_object_or_404(TrainingSessionRecord, pk=self.kwargs['pk'])

        individual_records = self.training_session_record.individual_records.all()
        kwargs.update({'individual_records': individual_records})
        return kwargs

    def form_valid(self, form):
        cleaned_data = form.cleaned_data
        if not hasattr(self, 'training_session_record'):
            self.training_session_record = get_object_or_404(TrainingSessionRecord, pk=self.kwargs['pk'])

        individual_records = self.training_session_record.individual_records.all()

        for field_name, attended in cleaned_data.items():
            if field_name.startswith('student_'):
                student_id = field_name.split('_')[1]
                try:
                    student = get_user_model().objects.get(pk=student_id)
                except get_user_model().DoesNotExist:
                    raise Http404

                try:
                    individual_record = individual_records.get(user=student)
                    individual_record.attended = attended
                    individual_record.save()
                except IndividualAttendanceRecord.DoesNotExist:
                    messages.error(self.request,
                                   f'حدث خطأ ما أثناء تسجيل حضور الطالب {student.full_name}. الرجاء المحاولة مرة أخرى')

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not hasattr(self, 'training_session_record'):
            self.training_session_record = get_object_or_404(TrainingSessionRecord, pk=self.kwargs['pk'])

        today = timezone.now().astimezone(pytz.timezone('Asia/Riyadh')).date()

        # Get the subscriptions for the division, annotated with the end_date,
        # so the expired subscriptions are can be highlighted

        individual_records = self.training_session_record.individual_records.all()
        users = [record.user for record in individual_records]

        subscriptions = self.training_session_record.division.subscriptions.filter(user__in=users).annotate(
            latest_end_date=Subquery(
                SubscriptionPeriod.objects.filter(
                    subscription=OuterRef('pk')
                ).order_by('-end_date').values('end_date')[:1]
            )
        ).annotate(attended=Subquery(
            IndividualAttendanceRecord.objects.filter(
                training_session_record_id=self.training_session_record,
                user=OuterRef('user')
            ).values('attended'), output_field=models.BooleanField()
        )).order_by('-latest_end_date')

        after_three_days = today + timezone.timedelta(days=3)

        context.update(
            {'today': today, 'subscriptions': subscriptions, 'division': self.training_session_record.division,
             'after_three_days': after_three_days, 'subs_today_sessions_active': True})
        return context


class PreviousRecordsList(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'subscriptions.add_trainingsessionrecord'
    template_name = 'attendance/previous_records.html'
    model = TrainingSessionRecord
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        queryset = (queryset
                    .annotate(students_count=Count('individual_records', distinct=True))
                    .annotate(attendance_count=Count('individual_records',
                                                     filter=Q(individual_records__attended=True),
                                                     distinct=True))
                    .order_by('-date'))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({'att_records_active': True})
        return context


class AttendanceRecordsView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'subscriptions.add_trainingsessionrecord'

    options = {
        'page-size': 'A4',
        'margin-top': '0.5in',
        'margin-right': '0.5in',
        'margin-bottom': '0.5in',
        'margin-left': '0.5in',
    }

    def get(self, request, pk):
        try:
            training_session = TrainingSessionRecord.objects.get(id=pk)
            training_session_individuals_records = training_session.individual_records.all()
            attended_count = training_session_individuals_records.filter(attended=True).count()

        except ObjectDoesNotExist:
            raise Http404

        time = timezone.now().astimezone(pytz.timezone('Asia/Riyadh')).strftime("%Y-%m-%d %H:%M")

        context = {
            'training_session': training_session,
            'individuals_records': training_session_individuals_records,
            'attended_count': attended_count,
            'time': time,
        }

        html = render_to_string('attendance/pdf_attendance_record.html', context)

        pdf = pdfkit.from_string(html, False, options=self.options)

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = \
            f'attachment; filename="attendance_record_{training_session.division.name}_{training_session.date}.pdf"'
        return response


class IndividualHistoryList(LoginRequiredMixin, ListView):
    template_name = 'attendance/individual_history.html'
    model = IndividualAttendanceRecord
    paginate_by = 10
    context_object_name = 'individual_records'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subscription = get_object_or_404(Subscription, pk=self.kwargs['pk'])

        summary = self.get_queryset().aggregate(overall_attendance=Count('id'),
                                                attended_count=Count('id', filter=Q(attended=True)))

        context.update({'subscription': subscription, 'summary': summary, 'subs_list_active': True})
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        thirty_days_ago = timezone.now().astimezone(pytz.timezone('Asia/Riyadh')) - timezone.timedelta(days=30)
        subscription = get_object_or_404(Subscription, pk=self.kwargs['pk'])
        queryset = (queryset.filter(user=subscription.user, training_session_record__division=subscription.division,
                                    training_session_record__date__gte=thirty_days_ago)
                    .order_by('-training_session_record__date'))
        return queryset
