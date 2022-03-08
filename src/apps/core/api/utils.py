import copy

from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import smart_str

from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class VerificationSerializer(serializers.Serializer):
    verification = serializers.SerializerMethodField(read_only=True)

    def get_verification(self, instance):
        if not instance.verifications.exists():
            ct = ContentType.objects.get_for_model(instance)
            model = instance.verifications.model

            verified = model.objects.filter(
                content_type__id=ct.id,
                is_valid=True,
                is_used=True
            ).last()
        else:
            verified = instance.verifications.last()

        return {
            'token': verified.token,
            'field': verified.field,
            'value': verified.value,
            'is_used': verified.is_used,
            'is_valid': verified.is_valid
        }


class ModelCleanMixin(serializers.BaseSerializer):
    def validate(self, attrs):
        super().validate(attrs)

        fields_name = [field.name for field in self.Meta.model._meta.fields]
        attrs_fields = [key for key, value in attrs.items()]
        attrs_non_model_field = []

        for field in attrs_fields:
            if field not in fields_name:
                attrs_non_model_field.append(field)

        if self.instance:
            for name in fields_name:
                value = getattr(self.instance, name)
                attr_value = attrs.get(name)
                if attr_value:
                    value = attr_value
                attrs.update({name: value})

        model_attrs = copy.deepcopy(attrs)
        if attrs_non_model_field:
            for field in attrs_non_model_field:
                try:
                    del model_attrs[field]
                except KeyError:
                    pass

        try:
            instance = self.Meta.model(**model_attrs)
            instance.clean()
        # Note that this raises Django's ValidationError Exception
        except ValidationError as e:
            raise serializers.ValidationError(smart_str(e))
        except KeyError:
            pass

        return attrs
