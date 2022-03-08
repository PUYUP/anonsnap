from rest_framework import serializers
from eav.models import Attribute


class AttributeSerializer(serializers.Serializer):
    slug = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Attribute.objects.all()
    )
    value_text = serializers.CharField(required=False)
    value_int = serializers.IntegerField(required=False)
    value_float = serializers.FloatField(required=False)
