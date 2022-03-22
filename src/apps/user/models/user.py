import uuid
from decimal import Decimal

from django.core.validators import RegexValidator
from django.db import models, transaction
from django.db.models import Q
from django.db.models.expressions import Exists, OuterRef, Subquery
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth.models import Group
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, FieldError

from apps.core.models.common import AbstractCommonField

from ..conf import settings
from ..validators import validate_msisdn


class UserManagerExtend(UserManager):
    @transaction.atomic
    def create_user(self, username, password, **extra_fields):
        return super().create_user(username, password=password, **extra_fields)

    def verification_check(self, *args, **kwargs):
        """
        Check verification for this user
        important field to check is;

        :ip_address
        :field
        :value
        """
        ct = ContentType.objects.get_for_model(self.model)
        verifications = getattr(self.model, 'verifications')
        model = verifications.field.related_model
        verified = model.objects.filter(
            content_type__id=ct.id,
            is_used=False,
            **kwargs
        ).last()

        if not verified:
            return False
        return True

    def get_active_user(self, *args, **kwargs):
        fields = ['email', 'msisdn']  # only use this fields (security reason)
        field = kwargs.get('field')
        value = kwargs.get('value')
        param = {'%s__iexact' % field: value, 'is_active': True}

        if field not in fields:
            raise FieldError(_("Field %s not exist." % field))
        return self.get_queryset().filter(**param)


# Extend User
# https://docs.djangoproject.com/en/3.1/topics/auth/customizing/#substituting-a-custom-user-model
class User(AbstractUser):
    guid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )
    hexid = models.CharField(max_length=255, editable=False, db_index=True)
    msisdn = models.CharField(
        db_index=True,
        blank=True,
        max_length=14,
        verbose_name=_("Phone number"),
        error_messages={
            'unique': _("A user with that msisdn already exists."),
        },
        validators=[validate_msisdn]
    )
    email = models.EmailField(
        _('email address'),
        db_index=True,
        blank=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        },
    )
    is_email_verified = models.BooleanField(default=False, null=True)
    is_msisdn_verified = models.BooleanField(default=False, null=True)

    objects = UserManagerExtend()
    verifications = GenericRelation(
        'core.Verification',
        related_query_name='user'
    )

    class Meta(AbstractUser.Meta):
        pass

    def check_users_exist(self):
        """We need verify email or msisdn if their has verified"""
        verifications_field = settings.USER_VERIFICATION_FIELDS
        if not verifications_field:
            raise ValidationError(_("User VERIFICATION_FIELDS not set."))

        q = Q()
        for field in verifications_field:
            value = getattr(self, field)
            if value:
                q |= Q(**{field: value})

        if q and self.__class__.objects.filter(q).exclude(id=self.pk).exists():
            raise ValidationError(
                _("%s used by another user." %
                  ' or '.join(verifications_field))
            )

    def clean(self, *args, **kwargs) -> None:
        self.check_users_exist()
        return super().clean()

    @property
    def name(self):
        full_name = '{}{}'.format(self.first_name, ' ' + self.last_name)
        return full_name if self.first_name else self.username

    @property
    def roles_by_group(self):
        group_annotate = self.groups.filter(name=OuterRef('name'))
        all_groups = self.groups.model.objects.all()
        user_groups = self.groups.all()

        # generate slug for group
        # ie is_group_name
        groups_role = {
            'is_{}'.format(slugify(v.name)): Exists(Subquery(group_annotate.values('name')[:1]))
            for i, v in enumerate(user_groups)
        }

        groups = all_groups.annotate(**groups_role)
        ret = dict()

        for group in groups:
            slug = 'is_%s' % slugify(group.name)
            ret.update({slug: getattr(group, slug, False)})
        return ret

    @property
    def get_verifications(self):
        verifications_field = settings.USER_VERIFICATION_FIELDS
        ct = ContentType.objects.get_for_model(self)
        model = self.verifications.model

        if not verifications_field:
            return model.objects.none()

        q_field_and_value = Q()
        q_challenge = Q()

        for field in verifications_field:
            value = getattr(self, field)
            if value:
                q_field_and_value |= Q(**{'field': field, 'value': value})
                q_challenge |= Q(**{'challenge': '%s_verification' % field})

        objs = model.objects.filter(
            q_field_and_value,
            q_challenge,
            content_type__id=ct.id,
            is_valid=True
        )

        return objs

    def has_verified(self):
        if self.get_verifications.filter(is_used=False).last():
            return True
        return False

    def is_verified(self):
        if self.get_verifications.filter(is_used=True).last():
            return True
        return False

    def mark_verification_used(self):
        obj = self.get_verifications.last()

        if obj:
            obj.is_used = True
            obj.save()

            # mark is_[xx]_verified
            mark_verified = getattr(self, 'mark_%s_verified' % obj.field)
            mark_verified()

    def send_verification(self):
        verifications_field = settings.USER_VERIFICATION_FIELDS

        for field in verifications_field:
            value = getattr(self, field)
            if value:
                self.verifications.create(
                    content_object=self,
                    field=field,
                    value=value,
                    challenge='%s_verification' % field,
                    sendwith=field,
                    sendto=value
                ).full_clean()

    def mark_email_verified(self):
        self.is_email_verified = True
        self.save(update_fields=['is_email_verified'])

    def mark_msisdn_verified(self):
        self.is_msisdn_verified = True
        self.save(update_fields=['is_msisdn_verified'])

    def unique_hexid(self):
        while True:
            object_id = id(timezone.now().timestamp())
            hexid = hex(object_id)

            if not self._meta.model.objects.filter(hexid=hexid).exists():
                return hexid

    def save(self, *args, **kwargs) -> None:
        # generate hex from guid
        if not self.id:
            self.hexid = self.unique_hexid()

        return super().save(*args, **kwargs)


class AbstractProfile(AbstractCommonField):
    class GenderChoice(models.TextChoices):
        UNDEFINED = 'unknown', _("Unknown")
        MALE = 'male', _("Male")
        FEMALE = 'female', _("Female")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    headline = models.CharField(max_length=255, null=True, blank=True)
    gender = models.CharField(
        choices=GenderChoice.choices,
        blank=True,
        null=True,
        default=GenderChoice.UNDEFINED,
        max_length=255,
        validators=[
            RegexValidator(
                regex='^[a-zA-Z_]*$',
                message=_("Can only contain the letters a-z and underscores."),
                code='invalid_identifier'
            ),
        ]
    )
    birthdate = models.DateField(blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    picture = models.ImageField(
        upload_to='profile',
        max_length=500,
        null=True,
        blank=True
    )
    address = models.TextField(blank=True, null=True)
    latitude = models.FloatField(default=Decimal(0.0), db_index=True)
    longitude = models.FloatField(default=Decimal(0.0), db_index=True)

    class Meta:
        abstract = True
        ordering = ['-user__date_joined']
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")

    def __str__(self):
        return self.name

    @property
    def name(self):
        full_name = '{}{}'.format(
            self.user.first_name, ' ' + self.user.last_name
        )
        return full_name if self.user.first_name else self.user.username


# Add custom field to group
Group.add_to_class('is_default', models.BooleanField(default=False))
