from django.apps import apps

from rest_framework import serializers

Tag = apps.get_registered_model('taggit', 'Tag')


class BaseTagSerializer(serializers.ModelSerializer):
    name = serializers.StringRelatedField()
    count = serializers.IntegerField(default=0)
    distance = serializers.FloatField(default=0)

    class Meta:
        model = Tag
        fields = ['name', 'count', 'distance', ]


class ListTagSerializer(BaseTagSerializer):
    class Meta(BaseTagSerializer.Meta):
        pass
