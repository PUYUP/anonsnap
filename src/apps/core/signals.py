from django.db import transaction
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
            # tasks.sendwith_sms.delay(data)
            pass

        elif instance.sendwith == sendwith.EMAIL:
            # tasks.sendwith_email.delay(data)
            pass
