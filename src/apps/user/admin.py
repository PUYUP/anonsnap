from django.apps import apps
from django.contrib import admin
from django.contrib.admin.filters import DateFieldListFilter
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .forms import UserChangeFormExtend, UserCreationFormExtend

User = apps.get_registered_model('user', 'User')
Profile = apps.get_registered_model('user', 'Profile')
Permission = apps.get_registered_model('auth', 'Permission')


class ProfileInline(admin.StackedInline):
    model = Profile


class UserExtend(UserAdmin):
    form = UserChangeFormExtend
    add_form = UserCreationFormExtend
    inlines = [ProfileInline, ]
    readonly_fields = ('hexid',)
    list_display = (
        'username',
        'first_name',
        'email',
        'is_email_verified',
        'msisdn',
        'is_msisdn_verified',
        'is_staff'
    )
    list_filter = UserAdmin.list_filter + \
        (('date_joined', DateFieldListFilter), 'last_login',)
    fieldsets = (
        (None, {'fields': ('hexid', 'username', 'password', 'email',
                           'is_email_verified', 'msisdn',
                           'is_msisdn_verified',)}),
        (_("Personal info"), {'fields': ('first_name', 'last_name',)}),
        (_("Permissions"), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups',),
        }),
        (_("Important dates"), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'fields': ('username', 'email', 'is_email_verified',
                       'msisdn', 'is_msisdn_verified',
                       'password1', 'password2', 'groups',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        queryset = qs \
            .prefetch_related('profile') \
            .select_related('profile')
        return queryset


admin.site.register(User, UserExtend)
