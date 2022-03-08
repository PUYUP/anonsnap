import uuid
from django.db import models


class AbstractCommonField(models.Model):
    guid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
