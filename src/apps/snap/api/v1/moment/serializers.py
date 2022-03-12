from django.apps import apps
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import serializers
from taggit.serializers import (
    TagListSerializerField,
    TaggitSerializer
)

from ..attachment.serializers import ListAttachmentSerializer
from ..location.serializers import ListLocationSerializer

UserModel = get_user_model()
Moment = apps.get_registered_model('snap', 'Moment')
Attachment = apps.get_registered_model('snap', 'Attachment')
Location = apps.get_registered_model('snap', 'Location')
With = apps.get_registered_model('snap', 'With')


class BaseMomentSerializer(TaggitSerializer, serializers.ModelSerializer):
    class Meta:
        model = Moment
        fields = '__all__'


class ListMomentSerializer(BaseMomentSerializer):
    _links = serializers.SerializerMethodField()
    user = serializers.StringRelatedField()
    tags = TagListSerializerField()
    withs = serializers.StringRelatedField(many=True)
    locations = ListLocationSerializer(many=True)
    attachments = ListAttachmentSerializer(
        many=True,
        fields=['name', 'file', ]
    )
    distance = serializers.FloatField(default=0)
    total_comment = serializers.IntegerField(default=0)
    is_owner = serializers.BooleanField(default=False)

    class Meta(BaseMomentSerializer.Meta):
        fields = [
            '_links',
            'guid',
            'user',
            'title',
            'summary',
            'create_at',
            'locations',
            'attachments',
            'tags',
            'withs',
            'distance',
            'total_comment',
            'is_owner',
        ]

    def get__links(self, instance):
        request = self.context.get('request')
        reverse_uri = reverse(
            'snap_api:moment-detail',
            kwargs={'guid': instance.guid}
        )
        absolute_uri = request.build_absolute_uri(reverse_uri)
        return absolute_uri


class RetrieveMomentSerializer(ListMomentSerializer):
    _links = serializers.ReadOnlyField()

    class Meta(ListMomentSerializer.Meta):
        pass

    def to_representation(self, instance):
        request = self.context.get('request')
        data = super().to_representation(instance)
        data.update({'is_owner': instance.user.id == request.user.id})
        return data


class CreateMomentSerializer(BaseMomentSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    locations = serializers.SlugRelatedField(
        many=True,
        slug_field='guid',
        queryset=Location.objects.filter(
            content_type__isnull=True,
            object_id__isnull=True
        )
    )
    attachments = serializers.SlugRelatedField(
        many=True,
        required=False,
        slug_field='guid',
        queryset=Attachment.objects.filter(
            content_type__isnull=True,
            object_id__isnull=True
        )
    )
    withs = serializers.SlugRelatedField(
        many=True,
        required=False,
        slug_field='username',
        queryset=UserModel.objects.all()
    )

    class Meta(BaseMomentSerializer.Meta):
        fields = [
            'title',
            'summary',
            'user',
            'locations',
            'attachments',
            'withs',
        ]

    def validate_user(self, value):
        if value.is_anonymous:
            return None
        return value

    def to_representation(self, instance):
        serializer = RetrieveMomentSerializer(
            instance=instance,
            context=self.context
        )
        return serializer.data

    def create(self, validated_data):
        locations = validated_data.pop('locations', None)
        attachments = validated_data.pop('attachments', None)
        withs = validated_data.pop('withs', None)

        instance = self.Meta.model.objects.create(**validated_data)
        if instance:
            if locations:
                instance.locations.set(locations)
            if attachments:
                instance.attachments.set(attachments)
            if withs:
                instance.withs.set(withs)

        return instance


class UpdateMomentSerializer(CreateMomentSerializer):
    class Meta(CreateMomentSerializer.Meta):
        fields = [
            'title',
            'summary',
            'locations',
            'attachments',
            'withs',
        ]

    def update(self, instance, validated_data):
        locations = validated_data.pop('locations', None)
        attachments = validated_data.pop('attachments', None)
        withs = validated_data.pop('withs', None)

        if locations:
            instance.locations.set(locations)
        if attachments:
            instance.attachments.set(attachments)
        if withs:
            instance.withs.set(withs)

        return super().update(instance, validated_data)
