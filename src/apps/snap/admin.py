from django.contrib import admin
from django.contrib.contenttypes import admin as ct_admin

from .models import *


class AttachmentInline(ct_admin.GenericStackedInline):
    model = Attachment
    ct_field = 'content_type'
    ct_fk_field = 'object_id'


class LocationInline(ct_admin.GenericStackedInline):
    model = Location
    ct_field = 'content_type'
    ct_fk_field = 'object_id'
    min_num = 1
    max_num = 1


class WithInline(admin.StackedInline):
    model = With


class MomentAdmin(admin.ModelAdmin):
    model = Moment
    inlines = (LocationInline, AttachmentInline, WithInline, )


class AttachmentAdmin(admin.ModelAdmin):
    model = Attachment
    inlines = (LocationInline,)


class CommentTreeInline(admin.StackedInline):
    model = CommentTree
    fk_name = 'child'


class CommentAdmin(admin.ModelAdmin):
    model = Comment
    inlines = (CommentTreeInline,)


admin.site.register(Moment, MomentAdmin)
admin.site.register(Attachment, AttachmentAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(CommentTree)
admin.site.register(Location)
admin.site.register(With)
