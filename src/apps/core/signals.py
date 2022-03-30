from django.db import transaction
from django.conf import settings
from . import tasks


@transaction.atomic
def verification_handler(sender, instance, created, **kwargs):
    sendwith = instance.__class__.SendWithOption
    sendmime = instance.__class__.SendMimeOption

    data = {
        'sendto': instance.sendto,
        'passcode': instance.passcode
    }

    if created and instance.sendmime == sendmime.TEXT:
        # send on created only
        if instance.sendwith == sendwith.MSISDN:
            if settings.DEBUG:
                tasks.sendwith_sms(data)
            else:
                tasks.sendwith_sms.delay(data)

        elif instance.sendwith == sendwith.EMAIL:
            # add from email
            data.update(
                {'from_email': '"AnonSnap!" <noreply@anonsnap.com>'}
            )

            if settings.DEBUG:
                tasks.sendwith_email(data)
            else:
                tasks.sendwith_email.delay(data)
