# https://pypi.org/project/django-appconf/
from django.conf import settings  # noqa
from appconf import AppConf


class CoreAppConf(AppConf):
    SMS_API_KEY = 'BUtyekOTMA3woP09cbh6VnAkAI2fxmd8LTqaFheQgJ4='
    SMS_CLIENT_ID = 'd973df88-5df9-4dc0-ba71-79939aae16e8'
    SMS_SENDER_ID = 'TCASTSMS'
    SMS_ENDPOINT = 'https://api.tcastsms.net/api/v2/SendSMS'

    class Meta:
        perefix = 'core'
