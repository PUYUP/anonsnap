# https://pypi.org/project/django-appconf/
from django.conf import settings  # noqa
from appconf import AppConf


class UserAppConf(AppConf):
    # user can choice use `email` or `msisdn`
    VERIFICATION_FIELDS = ['email', 'msisdn']

    # user must verify their owned `email` or `msisdn`
    # such as via OTP or not
    VERIFICATION_REQUIRED = False

    class Meta:
        perefix = 'user'
