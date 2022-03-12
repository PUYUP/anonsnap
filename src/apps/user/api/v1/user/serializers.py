from ipaddress import ip_address
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

from apps.core.api.utils import ModelCleanMixin, VerificationSerializer
from apps.core.utils import get_ip_address
from apps.user.helpers import generate_username
from apps.user.conf import settings
from ..profile.serializers import RetrieveProfileSerializer

UserModel = get_user_model()
verification_required = settings.USER_VERIFICATION_REQUIRED


class BaseUserSerializer(ModelCleanMixin, serializers.ModelSerializer):
    # Each static custom field must read_only
    profile = RetrieveProfileSerializer(
        read_only=True,
        many=False,
        required=False
    )

    class Meta:
        model = UserModel
        fields = '__all__'


class DynamicFieldsSerializer(BaseUserSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super(DynamicFieldsSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class ListUserSerializer(BaseUserSerializer):
    permalink = serializers.HyperlinkedIdentityField(
        view_name='user_api:user-detail',
        lookup_field='hexid'
    )

    class Meta(BaseUserSerializer.Meta):
        fields = ('permalink', 'hexid', 'name', 'username', 'profile',)


class RetrieveUserSerializer(DynamicFieldsSerializer, VerificationSerializer):
    class Meta(DynamicFieldsSerializer.Meta):
        fields = ('hexid', 'name', 'username', 'email',
                  'is_email_verified', 'msisdn', 'is_msisdn_verified',
                  'profile', 'verification',)


class CreateUserSerializer(BaseUserSerializer):
    # Each custom field must write_only
    # will return error at serializer because field not exists in model
    retype_password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )

    # acquired from `verification`
    # maybe from user its saved to cookie/locastorage
    passcode = serializers.CharField(required=verification_required)
    token = serializers.CharField(required=verification_required)

    class Meta(BaseUserSerializer.Meta):
        fields = ('email', 'msisdn', 'username', 'password',
                  'retype_password', 'first_name', 'passcode',
                  'token',)
        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'allow_blank': True, 'required': False},
        }

    def remove_non_user_fields(self, validated_data):
        user_fields = [field.name for field in UserModel._meta.fields]
        validated_fields = [key for key, _value in validated_data.items()]
        non_user_fields = [
            field for field in validated_fields if field not in user_fields
        ]

        for non_field in non_user_fields:
            validated_data.pop(non_field, None)
        return validated_data

    def validate_password(self, value):
        if self.initial_data.get('retype_password', None) != value:
            raise serializers.ValidationError(_("Password mismatch."))
        return value

    def validate_verification(self, field, attrs):
        passcode = self.initial_data.get('passcode')
        token = self.initial_data.get('token')

        # check verification
        # verification created and validated by `core` apps
        if field:
            request = self.context.get('request')
            ip = get_ip_address(request)
            value = attrs.get(field)

            verify = {
                'value': value,
                'field': field,
                'ip_address': ip
            }

            if passcode or token:
                verify.update({
                    'passcode': passcode,
                    'token': token,
                })

            # warning! brute force maybe can acquired user verification
            # case; user A verify their email but not used for signup
            # then user B maybe can used email from user A
            # so we need add some verification data like token
            verified = self.Meta.model.objects.verification_check(**verify)
            if not verified:
                not_validate = {field: _("%s not validate" % value)}
                raise serializers.ValidationError({**not_validate})

    def validate(self, attrs):
        super().validate(attrs)

        """Check verification fields exist in attrs"""
        verification_fields = settings.USER_VERIFICATION_FIELDS
        attr_fields = [field for field in attrs]

        # matches field
        matches = list(set(verification_fields).intersection(set(attr_fields)))

        # one of `msisdn` and `email` required
        if not matches:
            raise serializers.ValidationError(
                detail={
                    'field': _("%s required" % ' or '.join(verification_fields))
                }
            )

        # can't use both `email` and `msisdn`
        if len(matches) > 1:
            raise serializers.ValidationError(
                detail={'field': _("Can't use both %s" % ', '.join(matches))}
            )

        # validate verification if required
        if settings.USER_VERIFICATION_REQUIRED:
            field = matches[0]
            self.validate_verification(field, attrs)

        return attrs

    def to_internal_value(self, data):
        first_name = data.get('first_name')
        username = data.get('username')

        if not first_name or not username:
            if not username:
                auto_username = generate_username(first_name)
                data.update({'username': auto_username})

            if not first_name:
                data.update({'first_name': username})

        return super().to_internal_value(data)

    def to_representation(self, instance):
        serializer = RetrieveUserSerializer(
            instance,
            many=False,
            context=self.context
        )
        return serializer.data

    @transaction.atomic
    def create(self, validated_data):
        retype_password = validated_data.pop('retype_password')  # not used
        validated_data.update({'password': retype_password})

        # remove not user fields
        # if not will raise 'unexpected keyword argument <field_name>'
        validated_data = self.remove_non_user_fields(validated_data)

        # ready to create user
        instance = UserModel.objects.create_user(**validated_data)
        instance.mark_verification_used()
        return instance


class UpdateUserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = ('email', 'msisdn', 'username',)

    def to_representation(self, instance):
        serializer = RetrieveUserSerializer(
            instance,
            many=False,
            context=self.context
        )
        return serializer.data


class TokenObtainPairSerializerExtend(TokenObtainPairSerializer):
    def validate(self, attrs):
        context = {}
        data = super().validate(attrs)
        user = RetrieveUserSerializer(
            self.user,
            many=False,
            context=self.context
        )

        context.update({
            'token': data,
            'user': user.data
        })
        return context
