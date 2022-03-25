from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.utils.translation import gettext_lazy as _

from taggit.managers import TaggableManager

from apps.core.models.common import AbstractCommonField
from ..conf import settings
from .utils import SetMomentTags


class AbstractMoment(SetMomentTags, AbstractCommonField):
    title = models.CharField(
        db_index=True,
        max_length=255,
        null=True,
        blank=True
    )
    summary = models.TextField(null=True, blank=True)

    # non-registered user can make moment as anonym
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='moments',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    locations = GenericRelation('snap.Location', related_query_name='moment')
    attachments = GenericRelation(
        'snap.Attachment',
        related_query_name='moment'
    )
    comments = GenericRelation('snap.Comment', related_query_name='moment')
    reactions = GenericRelation('snap.Reaction', related_query_name='moment')
    tags = TaggableManager(
        verbose_name=_("Tags"),
        related_name='moment',
        help_text=_("Separate with comma if more than one."),
        blank=True
    )
    withs = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='snap.With',
        related_name='moment'
    )

    class Meta:
        abstract = True
        ordering = ['-create_at']

    def __str__(self) -> str:
        return self.title or self.summary or self.id


class AbstractWith(AbstractCommonField):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    moment = models.ForeignKey('snap.Moment', on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.user.name
