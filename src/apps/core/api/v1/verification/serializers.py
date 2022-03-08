from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.exceptions import NotFound

from apps.core.api.utils import ModelCleanMixin
from apps.core.utils import get_ip_address

Verification = apps.get_registered_model('core', 'Verification')


class BaseVerificationSerializer(ModelCleanMixin, serializers.ModelSerializer):
    class Meta:
        model = Verification
        fields = '__all__'


class RetrieveVerificationSerializer(BaseVerificationSerializer):
    class Meta(BaseVerificationSerializer.Meta):
        fields = [
            'token',
            'field',
            'value',
            'sendto',
            'sendwith',
            'challenge',
            'is_valid',
            'is_used'
        ]


class CreateVerificationSerializer(BaseVerificationSerializer):
    class Meta(BaseVerificationSerializer.Meta):
        fields = [
            'content_type',
            'object_id',
            'content_object',
            'field',
            'value',
            'challenge',
            'sendwith',
            'sendto'
        ]

    def to_internal_value(self, data):
        content_type = data.pop('content_type', None)

        try:
            ct = ContentType.objects.get(model=content_type)
        except ObjectDoesNotExist:
            raise serializers.ValidationError({
                'content_type': _("%s not registered" % content_type)
            })

        data.update({'content_type': ct.id})
        return super().to_internal_value(data)

    def to_representation(self, instance):
        serializer = RetrieveVerificationSerializer(
            instance,
            context=self.context
        )

        return serializer.data

    def create(self, validated_data):
        request = self.context.get('request')
        ip = get_ip_address(request)
        instance = self.Meta.model.objects \
            .generate(ip_address=ip, **validated_data)
        return instance


class ValidateVerificationSerializer(BaseVerificationSerializer):
    token = serializers.CharField(required=True)

    class Meta(BaseVerificationSerializer.Meta):
        fields = ['token', 'challenge']
        extra_kwargs = {
            'token': {'allow_null': False}
        }

    def to_representation(self, instance):
        serializer = RetrieveVerificationSerializer(
            instance,
            context=self.context
        )

        return serializer.data

    def validate(self, attrs):
        request = self.context.get('request')
        ip = get_ip_address(request)

        attrs.update({'ip_address': ip})

        instances = self.instance.filter(**attrs)
        if not instances.exists():
            raise NotFound()

        self.instance = instances.first()
        return super().validate(attrs)

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.mark_valid()
        return instance
