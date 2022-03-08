from django.apps import apps
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from rest_framework import serializers

Profile = apps.get_model('user', 'Profile')


class BaseProfileSerializer(serializers.ModelSerializer):
    # from user instance
    name = serializers.CharField()

    class Meta:
        model = Profile
        fields = '__all__'


class RetrieveProfileSerializer(BaseProfileSerializer):
    pass


class UpdateProfileSerializer(BaseProfileSerializer):
    first_name = serializers.CharField(required=False)

    class Meta(BaseProfileSerializer.Meta):
        fields = ('first_name', 'headline', 'gender', 'birthdate', 'about',
                  'picture', 'address', 'latitude', 'longitude',)

    def validate_picture(self, value):
        fsize = value.size
        fsize_mb = fsize/1000000
        fname = value.name

        # Can't larger than 2.5MB
        if fsize_mb > 2.5:
            raise serializers.ValidationError(
                {'picture': _("Max 2.5 MB. Your file %d MB" % fsize_mb)}
            )

        # Olny png, jpg an jpeg
        if not fname.endswith('.jpg') and not fname.endswith('.jpeg') and not fname.endswith('.png'):
            raise serializers.ValidationError(
                {'picture': _("Only .jpg, .jpeg and .png")}
            )

        return value

    def to_representation(self, instance):
        serializer = RetrieveProfileSerializer(instance, context=self.context)
        return serializer.data

    @transaction.atomic
    def update(self, instance, validated_data):
        user = getattr(instance, 'user', None)

        for key, value in validated_data.items():
            old_value = getattr(instance, key, None)
            if old_value != value:
                # update profile fields
                if hasattr(instance, key):
                    try:
                        setattr(instance, key, value)
                    except AttributeError:
                        pass

                # update user fields
                elif hasattr(user, key) and user:
                    try:
                        setattr(user, key, value)
                    except AttributeError:
                        pass

        if user:
            user.save(update_fields=['first_name'])

        instance.save()
        return instance
