from django.contrib import admin
from django.contrib.contenttypes import admin as ct_admin

from .models import *


class AttachmentInline(ct_admin.GenericStackedInline):
    model = Attachment
    ct_field = 'content_type'
    ct_fk_field = 'object_id'
    fields = ['id', 'file', 'name', 'identifier', 'caption', ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('user', 'content_type') \
            .select_related('user', 'content_type')


class LocationInline(ct_admin.GenericStackedInline):
    model = Location
    ct_field = 'content_type'
    ct_fk_field = 'object_id'
    min_num = 1
    max_num = 1
    fields = ['id', 'name', 'formatted_address', 'postal_code',
              'latitude', 'longitude', ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('user', 'content_type') \
            .select_related('user', 'content_type')


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
admin.site.register(Reaction)
