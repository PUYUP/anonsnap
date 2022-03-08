import logging
import requests

from django.utils.translation import gettext_lazy as _
from django.utils.encoding import smart_str
from django.core.mail import BadHeaderError, send_mail

from celery import shared_task
from apps.core.conf import settings


@shared_task
def sendwith_email(data):
    sendto = data.get('sendto')
    passcode = data.get('passcode')

    subject = _("Verification Code")
    from_email = data.get('from_email', 'noreply@example.com')
    message = _("Do not share to everyone. Verification code: %s" % passcode)

    if sendto and passcode:
        try:
            send_mail(subject, message, from_email, [sendto])
        except BadHeaderError:
            logging.info(_("Invalid header found."))
    else:
        # In reality we'd use a form class
        # to get proper validation errors.
        return logging.info(_("Make sure all fields are entered and valid."))


@shared_task
def sendwith_sms(data):
    sendto = data.get('sendto')
    passcode = data.get('passcode')
    message = _("Do not share to everyone. Verification code: %s" % passcode)

    # remove zero from first place
    if sendto[0] == '0':
        sendto = sendto[1:]

    sendto = '%s%s' % ('62', sendto)
    payload = {
        "ApiKey": settings.CORE_SMS_API_KEY,
        "ClientId": settings.CORE_SMS_CLIENT_ID,
        "SenderId": settings.CORE_SMS_SENDER_ID,
        "Message": message,
        "MobileNumbers": sendto,
        "Is_Unicode": True,
        "Is_Flash": False
    }

    r = requests.get(settings.CORE_SMS_ENDPOINT, params=payload)
    logging.info(smart_str(r.status_code))
