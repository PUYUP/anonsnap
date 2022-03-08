from django.contrib import admin
from django.contrib.auth.models import Group
from taggit.admin import Tag

from .models import *


class VerificationAdmin(admin.ModelAdmin):
    model = Verification
    readonly_fields = ['token', 'passcode', 'valid_until', 'ip_address']
    search_fields = ['passcode']
    list_display = [
        'passcode',
        'token',
        'sendwith',
        'sendto',
        'field',
        'value',
        'challenge',
        'content_type',
        'is_used',
        'is_valid'
    ]


# Register your models here.
# admin.site.unregister(Tag)
admin.site.unregister(Group)
admin.site.register(Verification, VerificationAdmin)
