from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext_lazy as _
from django.apps import apps
from django.utils.encoding import smart_str
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

Attribute = apps.get_registered_model('eav', 'Attribute')
Moment = apps.get_registered_model('snap', 'Moment')


class Command(BaseCommand):
    help = _("Create required eav2 attributes")
    attribute_data = [
        {
            'slug': 'device_iccid',
            'name': 'Device ICCID',
            'datatype': Attribute.TYPE_TEXT
        },
        {
            'slug': 'device_imei',
            'name': 'Device IMEI',
            'datatype': Attribute.TYPE_TEXT
        },
        {
            'slug': 'device_imsi',
            'name': 'Device IMSI',
            'datatype': Attribute.TYPE_TEXT
        },
        {
            'slug': 'device_uuid',
            'name': 'Device UUID',
            'datatype': Attribute.TYPE_TEXT
        },
    ]

    @transaction.atomic
    def handle(self, *args, **kwargs):
        ct = ContentType.objects.filter(model=Moment._meta.model_name)

        try:
            for attr in self.attribute_data:
                defaults = {
                    'name': attr.get('name'),
                    'datatype': attr.get('datatype'),
                }
                attribute, _created = Attribute.objects \
                    .update_or_create(slug=attr.get('slug'), defaults=defaults)
                attribute.entity_ct.set(ct)

                self.stdout.write(
                    self.style.SUCCESS(
                        _("{} OK".format(attr.get('slug')))
                    )
                )
        except LookupError as e:
            raise CommandError(smart_str(e))

        self.stdout.write(
            self.style.SUCCESS(
                _("Successfully create default {} attributes".format(
                    Moment._meta.model_name))
            )
        )
