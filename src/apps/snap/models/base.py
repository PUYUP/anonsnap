import os

from decimal import Decimal
from django.db import models
from django.contrib.contenttypes.fields import (
    GenericForeignKey,
    GenericRelation
)
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from taggit.managers import TaggableManager
from eav.managers import EntityManager

from apps.core.models.common import AbstractCommonField
from ..conf import settings
from .utils import SetAttachmentTags


class AbstractLocation(AbstractCommonField):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='locations',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='locations',
        limit_choices_to=models.Q(app_label='snap'),
        null=True,
        blank=True
    )
    object_id = models.CharField(max_length=255, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    name = models.CharField(max_length=255, null=True, blank=True)
    formatted_address = models.TextField(null=True, blank=True)
    postal_code = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        db_index=True
    )

    latitude = models.FloatField(default=Decimal(0.0), db_index=True)
    longitude = models.FloatField(default=Decimal(0.0), db_index=True)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return '{}, {}'.format(self.latitude, self.longitude)


class AbstractAttachment(SetAttachmentTags, AbstractCommonField):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='attachments',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='attachments',
        limit_choices_to=models.Q(app_label='snap'),
        null=True,
        blank=True
    )
    object_id = models.CharField(max_length=255, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    file = models.FileField(
        upload_to='attachments/%Y/%m/%d',
        null=True,
        blank=True
    )
    filename = models.CharField(
        max_length=255,
        editable=False,
        null=True,
        blank=True
    )
    filepath = models.CharField(
        max_length=255,
        editable=False,
        null=True,
        blank=True
    )
    filesize = models.IntegerField(
        editable=False,
        null=True,
        blank=True
    )
    filemime = models.CharField(
        max_length=255,
        editable=False,
        null=True,
        blank=True
    )

    name = models.CharField(max_length=255, null=True, blank=True)
    identifier = models.CharField(max_length=255, null=True, blank=True)
    caption = models.TextField(null=True, blank=True)

    # need standalone attachment location
    # maybe user move from their chair for 5 meters
    # to take attachment (video or image)
    locations = GenericRelation(
        'snap.Location',
        related_query_name='attachment'
    )
    comments = GenericRelation(
        'snap.Comment',
        related_query_name='attachment'
    )
    tags = TaggableManager(
        verbose_name=_("Tags"),
        related_name='attachment',
        help_text=_("Separate with comma if more than one."),
        blank=True
    )

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.name and self.file:
            self.name = os.path.basename(self.file.name)

        if self.file:
            self.filesize = self.file.size

        super().save(*args, **kwargs)


class AbstractComment(AbstractCommonField):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='comments',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='comments',
        limit_choices_to=models.Q(app_label='snap')
    )
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey('content_type', 'object_id')
    comment_content = models.TextField()

    class Meta:
        abstract = True
        ordering = ['-create_at']

    def __str__(self) -> str:
        return self.comment_content

    @property
    def activity_creator(self):
        return self.activity.user.name


class AbstractCommentTree(AbstractCommonField):
    parent = models.ForeignKey(
        'snap.Comment',
        related_name='parent',
        on_delete=models.CASCADE
    )
    child = models.OneToOneField(
        'snap.Comment',
        related_name='child',
        on_delete=models.CASCADE
    )

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return 'parent: {parent} - child: {child}' \
            .format(parent=self.parent.id, child=self.child.id)
