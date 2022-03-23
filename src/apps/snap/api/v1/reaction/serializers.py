from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_str

from rest_framework import serializers

Reaction = apps.get_registered_model('snap', 'Reaction')


class BaseReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reaction
        fields = '__all__'


class RetrieveReactionSerializer(BaseReactionSerializer):
    object_guid = serializers.UUIDField(source='content_object.guid')

    class Meta(BaseReactionSerializer.Meta):
        fields = ['guid', 'object_guid', 'identifier', ]


class CreateReactionSerializer(BaseReactionSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    object_id = serializers.UUIDField()
    content_type = serializers.CharField()

    class Meta(BaseReactionSerializer.Meta):
        fields = [
            'user',
            'content_type',
            'object_id',
            'identifier',
        ]

    def validate_user(self, value):
        if value.is_anonymous:
            return None
        return value

    def to_representation(self, instance):
        serializer = RetrieveReactionSerializer(
            instance=instance,
            context=self.context
        )
        return serializer.data

    def to_internal_value(self, data):
        request = self.context.get('request')
        if request.method == 'PATCH':
            return super().to_internal_value(data)

        ct_str = data.get('content_type')
        object_id = data.get('object_id')

        try:
            content_type = ContentType.objects \
                .get(app_label='snap', model=ct_str)
        except ObjectDoesNotExist as e:
            raise serializers.ValidationError(
                detail={'content_type': smart_str(e)}
            )

        try:
            content_object = content_type \
                .get_object_for_this_type(guid=object_id)
        except ObjectDoesNotExist as e:
            raise serializers.ValidationError(
                detail={'object_id': smart_str(e)}
            )

        data = super().to_internal_value(data)
        data.update({
            'content_type': content_type,
            'object_id': content_object.id
        })

        return data

    def create(self, validated_data):
        instance, _created = self.Meta.model.objects \
            .get_or_create(**validated_data)

        return instance
