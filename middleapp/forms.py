from django import forms

from .models import Organization
from .validators import validate_tax_number, validate_commercial_register


class OrganizationForm(forms.ModelForm):
    tax_number = forms.CharField(validators=[validate_tax_number], label='الرقم الضريبي')
    commercial_register = forms.CharField(validators=[validate_commercial_register], label='السجل التجاري')

    class Meta:
        model = Organization
        fields = 'name', 'phone', 'address', 'city', 'tax_number', 'commercial_register', 'logo', 'background'
        labels = {
            'name': 'اسم النادي',
            'phone': 'رقم الهاتف',
            'address': 'العنوان',
            'city': 'المدينة',
            'logo': 'صورة الشعار',
            'background': 'صورة الخلفية',
        }
