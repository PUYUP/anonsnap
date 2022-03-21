from django.apps import apps
from rest_framework import serializers

from taggit.serializers import (
    TagListSerializerField,
    TaggitSerializer
)

from ..fields import DynamicFieldsModelSerializer
from ..location.serializers import ListLocationSerializer

Attachment = apps.get_registered_model('snap', 'Attachment')
Location = apps.get_registered_model('snap', 'Location')


class BaseAttachmentSerializer(TaggitSerializer, DynamicFieldsModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'


class ListAttachmentSerializer(BaseAttachmentSerializer):
    locations = ListLocationSerializer(many=True)
    tags = TagListSerializerField()

    class Meta(BaseAttachmentSerializer.Meta):
        fields = [
            'guid',
            'file',
            'caption',
            'locations',
            'tags',
        ]


class RetrieveAttachmentSerializer(ListAttachmentSerializer):
    class Meta(ListAttachmentSerializer.Meta):
        pass


class CreateAttachmentSerializer(BaseAttachmentSerializer):
    file = serializers.FileField(required=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    locations = serializers.SlugRelatedField(
        many=True,
        required=False,
        slug_field='guid',
        queryset=Location.objects.all()
    )

    class Meta(BaseAttachmentSerializer.Meta):
        fields = ('user', 'file', 'name', 'caption', 'locations',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = None

    def validate_user(self, value):
        if value.is_anonymous:
            return None
        return value

    def to_representation(self, instance):
        serializer = RetrieveAttachmentSerializer(
            instance=instance,
            context=self.context
        )

        return serializer.data

    def create(self, validated_data):
        locations = validated_data.pop('locations', None)

        self.instance = self.Meta.model.objects.create(**validated_data)
        if self.instance and locations:
            self.instance.locations.set(locations)

        return self.instance
