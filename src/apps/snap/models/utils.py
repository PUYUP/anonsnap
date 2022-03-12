import re
from django.db import transaction


def extract_tags(content):
    # extracting the tags
    return re.findall("#(\w+)", content)


class SetTags(object):
    @transaction.atomic
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # set tags after object created!
        self.set_tags()


class SetMomentTags(SetTags):
    def set_tags(self):
        content = ''

        if self.title:
            content += self.title

        if self.summary:
            content += self.summary

        if content:
            tags = extract_tags(content)
            if tags:
                self.tags.set(tags)

    @transaction.atomic
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # set tags after object created!
        self.set_tags()


class SetAttachmentTags(SetTags):
    def set_tags(self):
        tags_in_name = extract_tags(self.name)
        tags_in_caption = []
        if self.caption:
            tags_in_caption = extract_tags(self.caption)

        tags = tags_in_name + tags_in_caption
        if tags:
            self.tags.set(tags)
