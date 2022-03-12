from django.db import transaction, models
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.tokens import default_token_generator
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_bytes, smart_str
from django.utils.http import urlsafe_base64_encode
from django.apps import apps
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.http import urlsafe_base64_decode

from rest_framework import serializers
from rest_framework.exceptions import NotFound

from apps.core.utils import get_ip_address
from apps.user.conf import settings

UserModel = get_user_model()
Verification = apps.get_registered_model('core', 'Verification')


class ResetWithOption(models.TextChoices):
    EMAIL = 'email', _("Email")
    MSISDN = 'msisdn', _("MSISDN")


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()
    retype_password = serializers.CharField()

    def to_representation(self, instance):
        return {'detail': _("Change password successfully")}

    def validate_current_password(self, value):
        valid = self.instance.check_password(value)
        if not valid:
            raise serializers.ValidationError(
                detail=_("Wrong current password"))
        return value

    def validate_retype_password(self, value):
        new_password = self.initial_data.get('new_password')
        if new_password != value:
            raise serializers.ValidationError(
                _("The two password fields didn’t match.")
            )
        password_validation.validate_password(value, self.instance)
        return value

    def update(self, instance, validated_data):
        retype_password = validated_data.get('retype_password')
        instance.set_password(retype_password)
        instance.save()

        return validated_data


class PasswordResetSerializer(serializers.Serializer):
    resetwith = serializers.ChoiceField(choices=ResetWithOption.choices)
    value = serializers.CharField()

    def validate_resetwith(self, value):
        allowed_fields = settings.USER_VERIFICATION_FIELDS
        if value not in allowed_fields:
            raise serializers.ValidationError(
                detail=_("%s not acceptable." % value)
            )
        return value

    def get_users(self, resetwith, value):
        active_users = UserModel.objects \
            .get_active_user(field=resetwith, value=value)

        return active_users

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret.update(instance)
        return ret

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        resetwith = validated_data.get('resetwith')
        value = validated_data.get('value')
        ip = get_ip_address(request)
        users = self.get_users(resetwith, value)

        if not users.exists():
            raise NotFound(
                _("User with %s %s not found." % (resetwith, value))
            )

        user = users.first()
        verify_model = user.verifications.model
        ct = ContentType.objects.get_for_model(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # create verification
        verify_data = {
            'content_type': ct,
            'sendwith': resetwith,
            'sendto': value,
            'challenge': '%s_reset_password_verification' % resetwith,
            'ip_address': ip,
            'field': resetwith,
            'value': value,
        }

        verify_instance = verify_model.objects.generate(**verify_data)
        verify_result = {
            'uid': uid,
            'reset_token': default_token_generator.make_token(user),
            'verification_token': verify_instance.token,
            'sendto': verify_instance.sendto,
            'sendwith': verify_instance.sendwith,
            'challenge': verify_instance.challenge,
            'is_valid': verify_instance.is_valid,
            'is_used': verify_instance.is_used,
        }

        return {**validated_data, **verify_result}


class SerializerPasswordResetConfirm(serializers.Serializer):
    uid = serializers.CharField()
    reset_token = serializers.CharField()
    resetwith = serializers.CharField()
    passcode = serializers.CharField()  # insert by user
    verification_token = serializers.CharField()
    new_password = serializers.CharField()  # insert by user
    retype_password = serializers.CharField()  # insert by user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.verification = Verification.objects.none()
        self.user = self._get_user(self.initial_data.get('uid'))

    def _get_user(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            user = UserModel._default_manager.get(pk=uid)
        except (
            TypeError,
            ValueError,
            OverflowError,
            UserModel.DoesNotExist,
            DjangoValidationError,
        ):
            user = None
        return user

    def validate_passcode(self, value):
        """validate to verification"""
        request = self.context.get('request')
        resetwith = self.initial_data.get('resetwith')
        passcode = self.initial_data.get('passcode')
        verification_token = self.initial_data.get('verification_token')
        challenge = '%s_reset_password_verification' % resetwith
        ip = get_ip_address(request)

        data = {
            'challenge': challenge,
            'passcode': passcode,
            'token': verification_token,
            'field': resetwith,
            'ip_address': ip,
        }

        try:
            self.verification = Verification.objects.validate(**data)
        except DjangoValidationError as e:
            raise serializers.ValidationError(smart_str(e))

        return value

    def validate_retype_password(self, value):
        new_password = self.initial_data.get('new_password')
        if new_password != value:
            raise serializers.ValidationError(
                _("The two password fields didn’t match.")
            )
        password_validation.validate_password(value, self.user)
        return value

    @transaction.atomic
    def create(self, validated_data):
        reset_token = validated_data.get('reset_token')
        retype_password = validated_data.get('retype_password')

        if self.user is None:
            raise serializers.ValidationError(_("Invalid user"))

        # validate reset_token
        if not default_token_generator.check_token(self.user, reset_token):
            raise serializers.ValidationError(_("Invalid reset token"))

        self.user.set_password(retype_password)
        self.user.save()
        self.verification.mark_used()

        return validated_data
