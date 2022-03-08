import eav

from apps.core.utils import is_model_registered
from simple_history.models import HistoricalRecords

from .base import *
from .moment import *

__all__ = list()


if not is_model_registered('snap', 'Location'):
    class Location(AbstractLocation):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractLocation.Meta):
            pass

    __all__.append('Location')


if not is_model_registered('snap', 'Attachment'):
    class Attachment(AbstractAttachment):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractAttachment.Meta):
            pass

    __all__.append('Attachment')


if not is_model_registered('snap', 'Comment'):
    class Comment(AbstractComment):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractComment.Meta):
            pass

    __all__.append('Comment')


if not is_model_registered('snap', 'CommentTree'):
    class CommentTree(AbstractCommentTree):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractCommentTree.Meta):
            pass

    __all__.append('CommentTree')


if not is_model_registered('snap', 'Moment'):
    class Moment(AbstractMoment):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractMoment.Meta):
            pass

    __all__.append('Moment')


if not is_model_registered('snap', 'With'):
    class With(AbstractWith):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractWith.Meta):
            pass

    __all__.append('With')


# register eav
eav.register(Moment)
eav.register(Comment)
eav.register(Attachment)
