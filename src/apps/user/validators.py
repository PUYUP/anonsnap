import phonenumbers

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_msisdn(value):
    """
    Checks msisdn valid with locale format
    """
    if value:
        error_msg = _('Enter a valid msisdn number')

        if not value.isnumeric():
            raise ValidationError(error_msg)

        try:
            parsed = phonenumbers.parse(value, 'ID')
        except phonenumbers.NumberParseException as e:
            pass

        if phonenumbers.is_valid_number(parsed):
            error_msg = None

        if error_msg:
            raise ValidationError(error_msg)
    return value
