from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils.text import slugify

UserModel = get_user_model()


class AuthBackend(ModelBackend):
    """
    Login w/h username, msisdn or email
    If :msisdn or :email not verified only can use :username
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)

        # Login with username, email or msisdn
        # can't login with `email` or `msisdn` until that value verified
        is_verified = settings.USER_VERIFICATION_REQUIRED
        obtain = Q(username__iexact=username) \
            | Q(email__iexact=username) & Q(is_email_verified=is_verified) \
            | Q(msisdn__iexact=username) & Q(is_msisdn_verified=is_verified)

        try:
            # user = UserModel._default_manager.get_by_natural_key(username)
            # You can customise what the given username is checked against, here I compare to both username and email fields of the User model
            user = UserModel.objects.filter(obtain)
        except UserModel.DoesNotExist:
            # Run the default password tokener once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            UserModel().set_password(password)
        else:
            try:
                user = user.get(obtain)
            except UserModel.MultipleObjectsReturned:
                message = _(
                    "{} has used. "
                    "If this is you, use Forgot Password verify account".format(username))
                raise ValueError(message)
            except UserModel.DoesNotExist:
                return None

            if user and user.check_password(password) and self.user_can_authenticate(user):
                return user
        return super().authenticate(request, username, password, **kwargs)


def generate_username(full_name):
    name = list(slugify(full_name).replace('-', ''))
    username = ''.join(name[0:5])

    if UserModel.objects.filter(username=username).count() > 0:
        users = UserModel.objects \
            .filter(username__regex=r'^%s[0-9]{1,}$' % username) \
            .order_by('username') \
            .values('username')

        if len(users) > 0:
            last_number_used = list(
                map(
                    lambda x: int(x['username'].replace(username, '')),
                    users
                )
            )

            last_number_used.sort()
            last_number_used = last_number_used[-1]
            number = last_number_used + 1
            username = '%s%s' % (username, number)
        else:
            username = '%s%s' % (username, 1)

        return username
    return slugify(username)
