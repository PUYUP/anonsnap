from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, IntegrityError
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

Profile = apps.get_model('user', 'Profile')


@transaction.atomic
def user_save_handler(sender, instance, created, **kwargs):
    if created:
        # set default group
        try:
            group = Group.objects.get(is_default=True)
            group.user_set.add(instance)
        except ObjectDoesNotExist:
            pass

        # send verification
        # used if user NOT require validate `email` or `msisdn` at signup
        # user validate after account created
        if not instance.has_verified():
            instance.send_verification()

    # create Profile if not exist
    if not hasattr(instance, 'profile'):
        try:
            Profile.objects.create(user=instance)
        except IntegrityError:
            pass


@transaction.atomic
def group_save_handler(sender, instance, created, **kwargs):
    is_default = getattr(instance, 'is_default')
    if is_default:
        groups = Group.objects.exclude(id=instance.id)
        if groups.exists():
            groups.update(is_default=False)
