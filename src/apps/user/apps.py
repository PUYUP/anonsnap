from django.apps import AppConfig
from django.db.models.signals import post_save


class UserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.user'
    label = 'user'

    def ready(self):
        from django.conf import settings
        from django.contrib.auth.models import Group
        from .signals import user_save_handler, group_save_handler

        # User
        post_save.connect(user_save_handler, sender=settings.AUTH_USER_MODEL,
                          dispatch_uid='user_save_signal')

        # Group
        post_save.connect(group_save_handler, sender=Group,
                          dispatch_uid='group_save_signal')
