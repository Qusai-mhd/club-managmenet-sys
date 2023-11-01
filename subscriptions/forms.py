from django.forms import inlineformset_factory

from reservations.forms import DateInputWidget  # TODO: Remove This
from subscriptions.models import SportCategory, Division, Subscription, TrainingWeekDay

from django import forms
from django_select2 import forms as s2forms

from .queries import get_all_customers
from .validators import validate_phone


class UserWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "phone__contains",
        "full_name__icontains",
        'email__icontains'
    ]


class SubscriptionCreateForm(forms.ModelForm):
    user = forms.ModelChoiceField(required=True, queryset=get_all_customers(), widget=UserWidget, label='العميل')
    division = forms.ModelChoiceField(required=True, queryset=Division.objects.filter(suspended=False), label='الفئة')
    start_date = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}), label='تاريخ البدء')
    months_num = forms.IntegerField(required=True, initial=1, label='عدد الشهور', min_value=1)
    price = forms.DecimalField(required=True, decimal_places=2, max_digits=5, label='السعر لكل شهر', min_value=0)
    total_price = forms.DecimalField(required=False, decimal_places=2, max_digits=5, label='السعر الإجمالي',
                                     disabled=True)
    initial_paid_amount = forms.DecimalField(required=True, decimal_places=2, max_digits=5, initial=0,
                                             label='المبلغ المدفوع مقدما', min_value=0)

    def __init__(self, *args, **kwargs):
        enable_price_field = kwargs.pop('enable_price_field', False)
        super().__init__(*args, **kwargs)
        if not enable_price_field:
            self.fields['price'].disabled = True
            self.fields['price'].required = False

    class Meta:
        model = Subscription
        fields = 'user', 'division', 'start_date', 'months_num', 'price', 'total_price', 'initial_paid_amount'


class ExtendSubscriptionForm(forms.ModelForm):
    start_date = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}),
                                 label='تاريخ بدء الفترة الجديدة')
    months_num = forms.IntegerField(required=True, initial=1, label='عدد الشهور',min_value=1)
    initial_paid_amount = forms.DecimalField(required=True, decimal_places=2, max_digits=5, initial=0,
                                             label='المبلغ المدفوع مقدما', min_value=0)
    price = forms.DecimalField(required=True, decimal_places=2, max_digits=5, label='السعر لكل شهر', min_value=0)
    total_price = forms.DecimalField(required=False, decimal_places=2, max_digits=5, label='السعر الإجمالي',
                                     disabled=True)

    def __init__(self, *args, **kwargs):
        enable_price_field = kwargs.pop('enable_price_field', False)
        super().__init__(*args, **kwargs)
        if not enable_price_field:
            self.fields['price'].disabled = True
            self.fields['price'].required = False

    class Meta:
        model = Subscription
        fields = 'start_date', 'months_num', 'initial_paid_amount', 'price',


class CategoryForm(forms.ModelForm):
    class Meta:
        model = SportCategory
        fields = 'name',
        labels = {
            'name': 'اسم الرياضة',
        }


class DivisionForm(forms.ModelForm):
    category = forms.ModelChoiceField(required=True, queryset=SportCategory.objects.all(), label='الرياضة')
    default_month_price = forms.DecimalField(required=True, decimal_places=2, max_digits=5, min_value=0,
                                             label='قيمة الاشتراك الافتراضية')

    class Meta:
        model = Division
        fields = 'category', 'name', 'default_month_price', 'suspended'
        labels = {
            'name': 'الفئة',
            'suspended': 'متوقفة',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'ادخل اسم الفئة'}),
        }


class SubscriptionPaymentForm(forms.ModelForm):
    due_amount = forms.DecimalField(required=False, decimal_places=2, max_digits=5, label='المبلغ المتبقي',
                                    disabled=True)
    new_payment = forms.DecimalField(required=True, decimal_places=2, max_digits=5, label='المبلغ المدفوع', initial=0,
                                     min_value=1)

    class Meta:
        model = Subscription
        fields = 'due_amount', 'new_payment'


class SubscriptionSearchForm(forms.ModelForm):
    user = forms.ModelChoiceField(required=False, queryset=get_all_customers(), widget=UserWidget, label='العميل')
    division = forms.ModelChoiceField(required=False, queryset=Division.objects.all(), label='الفئة')
    expired = forms.ChoiceField(required=False, choices=[('all', 'الكل'), ('yes', 'منتهٍ'), ('no', 'صالح')],
                                label='صلاحية الاشتراك', widget=forms.RadioSelect)

    class Meta:
        model = Subscription
        fields = 'user', 'division', 'expired'


def get_division_trainingDay_inlineformset_factory(extra, can_delete=True, can_add=True):
    return inlineformset_factory(Division, TrainingWeekDay, fields=('day', 'start_time', 'end_time'), extra=extra,
                                 can_delete_extra=False, can_delete=can_delete, edit_only=(not can_add),
                                 labels={'start_time': 'وقت بداية التمرين', 'end_time': 'وقت نهاية التمرين',
                                         'DELETE': 'حذف'},
                                 widgets={'start_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
                                          'end_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'})})


class AttendanceForm(forms.Form):

    def __init__(self, *args, **kwargs):
        custom_form_fields = kwargs.pop('custom_form_fields')
        super().__init__(*args, **kwargs)
        for field in custom_form_fields:
            self.fields[field[0]] = forms.BooleanField(required=False, label=field[1])


class UpdateAttendanceForm(forms.Form):

    def __init__(self, *args, **kwargs):
        individual_records = kwargs.pop('individual_records', None)
        super().__init__(*args, **kwargs)
        if individual_records is not None:
            for record in individual_records:
                self.fields[f'student_{record.user.id}'] = forms.BooleanField(required=False,
                                                                              label=record.user.full_name,
                                                                              initial=record.attended)


class SubscriptionsReportForm(forms.Form):
    reportPeriod = forms.ChoiceField(required=True, choices=[('monthly', 'شهري'), ('yearly', 'سنوي'),
                                                             ('custom', 'تاريخ مخصص')],
                                     label='فترة التقرير', widget=forms.RadioSelect, initial='monthly')

    month = forms.ChoiceField(required=False, choices=[(1, 'يناير'), (2, 'فبراير'), (3, 'مارس'), (4, 'أبريل'),
                                                       (5, 'مايو'), (6, 'يونيو'), (7, 'يوليو'), (8, 'أغسطس'),
                                                       (9, 'سبتمبر'), (10, 'أوكتوبر'), (11, 'نوفمبر'),
                                                       (12, 'ديسمبر')], label='الشهر')

    year = forms.IntegerField(required=False, min_value=2000, max_value=2100, initial=2023, label='السنة')

    dayFrom = forms.DateField(required=False, input_formats=['%Y-%m-%d'], widget=DateInputWidget, label='من')
    dayTo = forms.DateField(required=False, input_formats=['%Y-%m-%d'], widget=DateInputWidget, label='إلى')
