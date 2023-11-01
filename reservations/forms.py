from django import forms
from django.forms import inlineformset_factory

from .models import Reservation, Facility, TimeSlot, FacilityCategory
from .queries import get_free_slots, get_all_facilities, get_weekly_free_slots, get_all_customers
from django_select2 import forms as s2forms

from django.forms import models as fModels
from django.forms.fields import ChoiceField


class DateInputWidget(forms.DateInput):
    input_type = 'date'


# class FacilityWidget(s2forms.ModelSelect2Widget):
#     search_fields = [
#         "name__icontains",
#     ]


class UserWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "phone__contains",
        "full_name__icontains",
        'email__icontains'
    ]


class AdvancedModelChoiceIterator(fModels.ModelChoiceIterator):
    """
    This iterator is used by AdvancedModelChoiceField to return a tuple of (value, label, obj) instead of (value, label)
    ie, it returns the model object as the third element in the tuple.
    This is useful when you want to access the model object of the choice in the template
    """

    def choice(self, obj):
        return self.field.prepare_value(obj), self.field.label_from_instance(obj), obj


class AdvancedModelChoiceField(fModels.ModelChoiceField):
    """
    This inherits from ModelChoiceField and uses the AdvancedModelChoiceIterator to return a tuple of
    (value, label, obj) instead of (value, label)
    """

    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices

        return AdvancedModelChoiceIterator(self)

    choices = property(_get_choices, ChoiceField._set_choices)


class ReservationForm1(forms.ModelForm):
    day = forms.DateField(required=True, input_formats=['%Y-%m-%d'], widget=DateInputWidget, label='التاريخ')
    facility = AdvancedModelChoiceField(required=True, queryset=Facility.objects.filter(suspended=False), widget=forms.RadioSelect,
                                        label='الملعب')

    class Meta:
        model = Reservation
        fields = ["facility", "day"]


class ReservationForm2(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        fac = kwargs.pop('fac', None)
        day = kwargs.pop('day', None)
        default_price = kwargs.pop('price', None)
        can_change_price = kwargs.pop('can_change_price', False)

        super(ReservationForm2, self).__init__(*args, **kwargs)

        self.fields['user'].label = 'العميل'
        self.fields['time_slot'].label = 'الفترة'
        self.fields['price'].label = 'السعر'

        if fac and day:
            self.fields['time_slot'].queryset = get_free_slots(fac, day)

        if default_price:
            self.fields['price'].initial = default_price

        if not can_change_price:
            self.fields['price'].widget.attrs['disabled'] = True
            self.fields['price'].required = False

    user = forms.ModelChoiceField(required=True, queryset=get_all_customers(), widget=UserWidget)

    class Meta:
        model = Reservation
        fields = ['user', 'time_slot', 'price']


class UpdateReservationForm1(forms.ModelForm):
    day = forms.DateField(required=True, input_formats=['%Y-%m-%d'], widget=DateInputWidget, label='التاريخ')

    def __init__(self, *args, **kwargs):
        old_reservation = kwargs.pop('old_reservation', None)
        super().__init__(*args, **kwargs)

        if old_reservation:
            self.fields['day'].initial = old_reservation.day

    class Meta:
        model = Reservation
        fields = ["day"]


class UpdateReservationForm2(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        old_reservation = kwargs.pop('old_reservation', None)
        freeSlots = kwargs.pop('freeSlots', None)
        can_change_price = kwargs.pop('can_change_price', False)

        super().__init__(*args, **kwargs)

        self.fields['time_slot'].label = 'الفترة'
        self.fields['price'].label = 'السعر'

        if old_reservation:
            self.fields['price'].initial = old_reservation.price
            self.fields['time_slot'].queryset = freeSlots

        if not can_change_price:
            self.fields['price'].widget.attrs['disabled'] = True
            self.fields['price'].required = False

    class Meta:
        model = Reservation
        fields = ['time_slot', 'price']


class WeeklyReservationForm1(forms.ModelForm):
    facility = AdvancedModelChoiceField(required=True, queryset=Facility.objects.filter(suspended=False), widget=forms.RadioSelect,
                                        label='الملعب')
    day = forms.DateField(required=True, input_formats=['%Y-%m-%d'], widget=DateInputWidget, label='تاريخ اليوم الأول')

    weeksNumber = forms.IntegerField(required=True, min_value=2, max_value=52, initial=2, label='عدد الأسابيع')

    class Meta:
        model = Reservation
        fields = ["facility", "day", 'weeksNumber']


class WeeklyReservationForm2(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        fac = kwargs.pop('fac', None)
        day = kwargs.pop('day', None)
        weeksNumber = kwargs.pop('weeksNumber', None)
        can_change_price = kwargs.pop('can_change_price', False)

        super().__init__(*args, **kwargs)

        self.fields['user'].label = 'العميل'
        self.fields['time_slot'].label = 'الفترة'
        self.fields['price'].label = 'السعر'

        if fac:
            self.fields['price'].initial = fac.default_price

            if day and weeksNumber:
                self.fields['time_slot'].queryset = get_weekly_free_slots(fac, day, weeksNumber)

        if not can_change_price:
            self.fields['price'].widget.attrs['disabled'] = True
            self.fields['price'].required = False

    user = forms.ModelChoiceField(required=True, queryset=get_all_customers(), widget=UserWidget)

    class Meta:
        model = Reservation
        fields = ['user', 'time_slot', 'price']


class ReservationSearchForm(forms.ModelForm):
    #  Search by day: a radio button widget, [searchByExactDay, searchByDayRange, searchBeforeDay, searchAfterDay]
    searchByDay = forms.ChoiceField(required=False,
                                    choices=[('exact', 'يوم معين'), ('range', 'فترة معينة'), ('before', 'قبل يوم معين'),
                                             ('after', 'بعد بوم معين')],
                                    widget=forms.RadioSelect, label='بحث التاريخ بحسب', initial='exact')

    day = forms.DateField(required=False, input_formats=['%Y-%m-%d'], widget=DateInputWidget, label='التاريخ')

    dayFrom = forms.DateField(required=False, input_formats=['%Y-%m-%d'], widget=DateInputWidget, label='من')
    dayTo = forms.DateField(required=False, input_formats=['%Y-%m-%d'], widget=DateInputWidget, label='إلى')

    searchByFacility = forms.ChoiceField(required=False,
                                         choices=[('facility', 'بحث عن ملعب معين'), ('category', 'بحث عن فئة ملاعب')],
                                         widget=forms.RadioSelect, label='بحث بحسب', initial='facility')

    facility = forms.ModelChoiceField(required=False, queryset=get_all_facilities(),
                                      label='الملعب')

    category = forms.ModelChoiceField(required=False, queryset=FacilityCategory.objects.all(), label='الفئة')

    gender = forms.ChoiceField(required=False,
                               choices=[('all', 'الكل'), ('male', 'ذكور'), ('female', 'إناث')],
                               widget=forms.RadioSelect, label='بحث العملاء بحسب', initial='all')

    user = forms.ModelChoiceField(required=False, queryset=get_all_customers(), widget=UserWidget, label='العميل')

    searchByPrice = forms.ChoiceField(required=False,
                                      choices=[('exact', 'مبلغ معين'), ('range', 'بين مبلغين'),
                                               ('less', 'أقل من'), ('greater', 'أكثر من')],
                                      widget=forms.RadioSelect, label='بحث السعر بحسب', initial='exact')

    price = forms.IntegerField(required=False, label='السعر')
    priceFrom = forms.IntegerField(required=False, label='من')
    priceTo = forms.IntegerField(required=False, label='إلى')

    class Meta:
        model = Reservation
        fields = ["searchByDay", "day", "dayFrom", "dayTo", 'searchByFacility', 'category', "facility", 'gender',
                  'user',
                  'searchByPrice', 'price', 'priceFrom', 'priceTo']


class ReportForm(forms.Form):
    reportType = forms.ChoiceField(required=True, choices=[('summary', 'تقرير ملخص'),
                                                           ('record', 'كشف الحجوزات')],
                                   label='نوع التقرير', widget=forms.RadioSelect, initial='summary')

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


def get_FTS_inlineformset_factory(extra, can_delete=True, can_add=True):
    return inlineformset_factory(Facility, TimeSlot, fields=('start_time', 'end_time'), extra=extra,
                                 can_delete_extra=False, can_delete=can_delete, edit_only=(not can_add),
                                 labels={'start_time': 'البداية', 'end_time': 'النهاية', 'DELETE': 'حذف'},
                                 widgets={'start_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
                                          'end_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'})})


class FacilityForm(forms.ModelForm):
    class Meta:
        model = Facility
        fields = 'name', 'category', 'default_price', 'suspended', 'image', 'color',
        labels = {
            'name': 'اسم الملعب',
            'category': 'الفئة',
            'default_price': 'السعر الافتراضي',
            'suspended': 'متوقف',
            'image': 'صورة الملعب',
            'color': 'لون عرض الحجوزات لهذا الملعب',
        }

        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = FacilityCategory
        fields = 'name',
        labels = {
            'name': 'اسم الفئة',
        }
