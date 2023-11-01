import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_phone(value):
    regex = re.compile(r'^05[0-9]{8}$')
    if not regex.match(value):
        raise ValidationError(
            _('يجب أن يكون رقم هاتف سعودي صحيح مثل:  0555555555'),
        )
