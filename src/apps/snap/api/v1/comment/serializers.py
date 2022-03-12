from django.apps import apps
from django.urls import reverse_lazy
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_str

from rest_framework import serializers

Comment = apps.get_registered_model('snap', 'Comment')
CommentTree = apps.get_registered_model('snap', 'CommentTree')


class BaseCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'


class ListCommentSerializer(BaseCommentSerializer):
    _links = serializers.SerializerMethodField()
    user = serializers.CharField()
    parent = serializers.IntegerField(
        read_only=True,
        source='child.parent.id'
    )

    class Meta(BaseCommentSerializer.Meta):
        fields = [
            '_links',
            'guid',
            'parent',
            'user',
            'comment_content',
        ]

    def get__links(self, instance):
        request = self.context.get('request')
        reverse_uri = reverse_lazy(
            'snap_api:comment-detail',
            kwargs={'guid': instance.guid}
        )
        absolute_uri = request.build_absolute_uri(reverse_uri)
        return absolute_uri


class RetrieveCommentSerializer(ListCommentSerializer):
    _links = serializers.ReadOnlyField()

    class Meta(ListCommentSerializer.Meta):
        pass


class CreateCommentSerializer(BaseCommentSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    object_id = serializers.UUIDField()
    content_type = serializers.CharField()
    parent = serializers.SlugRelatedField(
        slug_field='guid',
        queryset=Comment.objects.all(),
        required=False
    )

    class Meta(BaseCommentSerializer.Meta):
        fields = [
            'user',
            'content_type',
            'object_id',
            'comment_content',
            'parent',
        ]

    def validate_user(self, value):
        if value.is_anonymous:
            return None
        return value

    def to_representation(self, instance):
        serializer = RetrieveCommentSerializer(
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
        parent = validated_data.pop('parent', None)
        instance = super().create(validated_data)

        if parent:
            CommentTree.objects.create(parent=parent, child=instance)
        return instance


class UpdateCommentSerializer(CreateCommentSerializer):
    class Meta(CreateCommentSerializer.Meta):
        fields = ['comment_content', ]
