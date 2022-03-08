import pyotp
import phonenumbers

from django.db import models, transaction
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator, validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from .common import AbstractCommonField


class VerificationQuerySet(models.QuerySet):
    def queryset(self, *args, **kwargs):
        """Must not expired and not used"""
        lookup = [Q(**{k: kwargs.get(k, None)}) for k in kwargs.keys()]
        return self.select_for_update().filter(
            *lookup,
            Q(valid_until__gt=timezone.now()),
            Q(is_used=False)
        )

    def generate(self, *args, **kwargs):
        """Generate if valid_until greather than now"""
        instance, _created = self.filter(
            valid_until__gt=timezone.now(),
            is_valid=False,
            is_used=False
        ).update_or_create(**kwargs, defaults=kwargs)

        return instance

    @transaction.atomic
    def validate(self, *args, **kwargs):
        """Validate then mark as valid"""
        instance = self.queryset(**kwargs).last()
        if not instance:
            raise ValidationError(_("Verification invalid"))

        instance.mark_valid()
        instance.refresh_from_db()

        return instance


class AbstractVerification(AbstractCommonField):
    """
    Send Verification with;
        :email
        :msisdn (SMS or Voice Call)

    :valid_until; Verification validity max date (default 2 hour)
    """
    class SendWithOption(models.TextChoices):
        MSISDN = 'msisdn', _("MSISDN")
        EMAIL = 'email', _("Email")

    class SendMimeOption(models.TextChoices):
        TEXT = 'text', _("Text")
        VOICE = 'voice', _("Voice")

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='verifications'
    )
    object_id = models.CharField(max_length=255, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    field = models.CharField(max_length=255, help_text=_("Such as `email`"))
    value = models.CharField(max_length=255, help_text=_("myemail@domain.com"))
    challenge = models.SlugField(
        max_length=255,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z_][0-9a-zA-Z_]*$',
                message=_(
                    "Code can only contain the letters a-z, A-Z, digits, "
                    "and underscores, and can't start with a digit."
                )
            )
        ],
        help_text=_("Unique identifier, egg: email_verification")
    )

    sendwith = models.CharField(
        choices=SendWithOption.choices,
        max_length=255,
        null=True,
        blank=True
    )
    sendto = models.CharField(max_length=255, null=True, blank=True)
    sendmime = models.CharField(
        max_length=15,
        choices=SendMimeOption.choices,
        default=SendMimeOption.TEXT
    )

    token = models.CharField(max_length=64, editable=False, db_index=True)
    passcode = models.CharField(max_length=25, editable=False, db_index=True)
    valid_until = models.DateTimeField(blank=True, null=True, editable=False)
    valid_until_timestamp = models.PositiveBigIntegerField(editable=False)
    user_agent = models.TextField(null=True, blank=True)
    ip_address = models.CharField(max_length=255, null=True, blank=True)

    is_valid = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)

    objects = VerificationQuerySet.as_manager()

    class Meta:
        abstract = True
        verbose_name = _("Verification")
        verbose_name_plural = _("Verifications")

    def __str__(self):
        return self.passcode

    @property
    def is_expired(self) -> bool:
        return self.valid_until <= timezone.now()

    def clean(self) -> None:
        # check field exist in `content_type`
        ct_class = self.content_type.model_class()
        ct_model_name = ct_class._meta.model_name
        ct_fields = [field.name for field in ct_class._meta.fields]

        if self.field not in ct_fields:
            raise ValidationError(
                {
                    'field': _('Value: %s not exist in: %s'
                               % (self.field, ct_model_name))
                },
                code='invalid'
            )

        # check matching `sendwith` and `sendto`
        if self.sendwith:
            sendto_validator = getattr(self, '_validate_%s' % self.sendwith)
            sendto_validator(self.sendto)

        return super().clean()

    def _validate_msisdn(self, value):
        msisdn_number = phonenumbers.parse(value, 'ID')
        if not phonenumbers.is_valid_number(msisdn_number):
            raise ValidationError(
                {'sendto': _('Value: %s invalid number' % value)},
                code='invalid'
            )

    def _validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise ValidationError(
                {'sendto': _('Value: %s invalid email' % value)},
                code='invalid'
            )

    def _check_passcode_expired(self, *args, **kwargs):
        """Check passcode not expired"""
        otp = pyotp.TOTP(self.token)
        if not otp.verify(self.passcode, for_time=self.valid_until_timestamp):
            raise ValidationError(_("Passcode expired"))

    def _generate_passcode_and_token(self):
        # Set max validity date
        # Default 2 hours since created
        self.valid_until = timezone.now() + timezone.timedelta(hours=2)
        self.valid_until_timestamp = self.valid_until \
            .replace(microsecond=0) \
            .timestamp()

        # generate token
        self.token = pyotp.random_base32()

        # generate passcode from token
        totp = pyotp.TOTP(self.token)
        self.passcode = totp.at(self.valid_until_timestamp)

    def mark_valid(self):
        self._check_passcode_expired()

        self.is_valid = True
        self.save(update_fields=['is_valid'])

    def mark_used(self):
        if not self.is_valid:
            raise ValidationError(_("Passcode not validated"))

        self.is_used = True
        self.save(update_fields=['is_used'])

    def _email_reset_password_verification(self):
        """
        When reset password we check user exist
        Note: `email_reset_password_verification` is verification challenge
        """
        ct_class = self.content_type.model_class()
        ct_model = ct_class._meta.model
        kwargs = {
            'field': self.field,
            'value': self.value
        }

        users = ct_model.objects.get_active_user(**kwargs)
        if not users.exists():
            raise ValidationError(
                _("User with %s %s not exist." % (self.field, self.value))
            )

        # fill object_id with user_id
        user = users.first()
        self.object_id = user.id

    _msisdn_reset_password_verification = _email_reset_password_verification

    @transaction.atomic
    def save(self, *args, **kwargs):
        # re-generate passcode when re-save (update)
        if not self.is_used and not self.is_valid:
            self._generate_passcode_and_token()

        _method = '_%s' % self.challenge
        challenge_validator = getattr(self, _method, None)

        if challenge_validator:
            challenge_validator()

        super().save(*args, **kwargs)
