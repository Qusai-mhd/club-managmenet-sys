import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_tax_number(value):
    regex = re.compile(r'^\d{15}$')
    if not regex.match(value):
        raise ValidationError(
            _('يجب أن يكون رقم الضريبة صحيح مكون من 15 رقم'),
        )


def validate_commercial_register(value):
    regex = re.compile(r'^\d{14}$')
    if not regex.match(value):
        raise ValidationError(
            _('يجب أن يكون السجل التجاري صحيح مكون من 14 رقم'),
        )
