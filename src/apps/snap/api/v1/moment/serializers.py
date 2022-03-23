import re

from django.apps import apps
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from apps.snap.api.v1.reaction.serializers import RetrieveReactionSerializer
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

    def validate_locations(self, value):
        if not bool(value):
            raise serializers.ValidationError(
                detail=_("Location required")
            )
        return value

    def validate_attachments(self, value):
        if not bool(value):
            raise serializers.ValidationError(
                detail=_("Attachment (photo) required")
            )
        return value


class ListMomentSerializer(BaseMomentSerializer):
    _links = serializers.SerializerMethodField()
    user = serializers.StringRelatedField()
    tags = TagListSerializerField()
    withs = serializers.StringRelatedField(many=True)
    locations = ListLocationSerializer(many=True)
    attachments = ListAttachmentSerializer(
        many=True,
        fields=['file', 'guid', ]
    )
    distance = serializers.FloatField(default=None)
    user_distance = serializers.FloatField(default=None)
    comment_count = serializers.IntegerField(default=0)
    reactions = RetrieveReactionSerializer(many=True)
    reaction_count = serializers.IntegerField(default=0)
    is_owner = serializers.BooleanField(default=False)

    class Meta(BaseMomentSerializer.Meta):
        fields = [
            '_links',
            'id',
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
            'user_distance',
            'comment_count',
            'reaction_count',
            'reactions',
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

    def to_representation(self, instance):
        data = super().to_representation(instance)
        summary = data.get('summary')
        if summary:
            # replace '#hashtag' with '<span>#hashtag</span>'
            regex = r"#[a-zA-Z0-9]*"
            result = re.sub(
                regex,
                lambda m: '<span class="text-danger">{}</span>'.format(
                    m.group(0)),
                summary
            )

            data.update({'summary_html': result})
        return data


class RetrieveMomentSerializer(ListMomentSerializer):
    _links = serializers.ReadOnlyField()

    class Meta(ListMomentSerializer.Meta):
        pass

    def to_representation(self, instance):
        request = self.context.get('request')
        data = super().to_representation(instance)

        # only for POST and PATCH
        if 'GET' not in request.method:
            attachments = instance.attachments.order_by('-create_at')
            data.update({
                'is_owner': instance.user.id == request.user.id,
                'attachments': ListAttachmentSerializer(
                    attachments,
                    many=True,
                    fields=['file', 'guid', ],
                    context=self.context
                ).data,

                # of course distance from location creator is zero
                'user_distance': 0,
                'distance': 0,
            })

        return data


class CreateMomentSerializer(BaseMomentSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    locations = serializers.SlugRelatedField(
        many=True,
        slug_field='guid',
        queryset=Location.objects.all()
    )
    attachments = serializers.SlugRelatedField(
        many=True,
        slug_field='guid',
        queryset=Attachment.objects.all()
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
