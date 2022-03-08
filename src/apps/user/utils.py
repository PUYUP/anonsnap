import unicodedata

from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def unicode_ci_compare(s1, s2):
    """
    Perform case-insensitive comparison of two identifiers, using the
    recommended algorithm from Unicode Technical Report 36, section
    2.11.2(B)(2).
    """
    return unicodedata.normalize('NFKC', s1).casefold() == unicodedata.normalize('NFKC', s2).casefold()


def get_users(obtain):
    UserModel = get_user_model()

    """Given an email or msisdn, return matching user(s) who should receive a reset.
        This allows subclasses to more easily customize the default policies
        that prevent inactive users and users with unusable passwords from
        resetting their password.
        """
    email_field_name = UserModel.get_email_field_name()
    msisdn_field_name = 'msisdn'

    users = UserModel._default_manager.filter(
        Q(**{'%s__iexact' % email_field_name: obtain})
        | Q(**{'%s__iexact' % msisdn_field_name: obtain})
    )

    return (
        u for u in users
        if u.has_usable_password() and
        (
            unicode_ci_compare(obtain, getattr(u, email_field_name))
            or unicode_ci_compare(obtain, getattr(u, msisdn_field_name))
        )
    )


def get_password_recovery_token_uidb64(obtain):
    """
    :obtain can use :msisdn or :email
    Return token and uidb64 or not found error
    """
    token = None
    uidb64 = None
    for user in get_users(obtain):
        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        break

    if not token and not uidb64:
        raise ValueError('User not found')
    return token, uidb64
