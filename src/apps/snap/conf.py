# https://pypi.org/project/django-appconf/
from django.conf import settings  # noqa
from appconf import AppConf


class SnapAppConf(AppConf):
    class Meta:
        perefix = 'snap'
