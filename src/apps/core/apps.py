from django.apps import AppConfig
from django.db.models.signals import post_save


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    label = 'core'

    def ready(self) -> None:
        from . import signals
        from . import models

        post_save.connect(
            signals.verification_handler,
            dispatch_uid='verification_handler',
            sender=models.Verification
        )
