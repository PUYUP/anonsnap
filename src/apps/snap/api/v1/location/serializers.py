from django.apps import apps
from rest_framework import serializers

Location = apps.get_registered_model('snap', 'Location')


class BaseLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'


class ListLocationSerializer(BaseLocationSerializer):
    class Meta(BaseLocationSerializer.Meta):
        fields = [
            'guid',
            'name',
            'formatted_address',
            'postal_code',
            'latitude',
            'longitude'
        ]


class CreateLocationSerializer(BaseLocationSerializer):
    class Meta(BaseLocationSerializer.Meta):
        fields = [
            'name',
            'formatted_address',
            'postal_code',
            'latitude',
            'longitude'
        ]

    def to_representation(self, instance):
        serializer = ListLocationSerializer(
            instance=instance,
            context=self.context
        )

        return serializer.data
