from apps.core.utils import is_model_registered
from simple_history.models import HistoricalRecords

from .user import *

__all__ = list()


# https://docs.djangoproject.com/en/3.1/topics/auth/customizing/#auth-custom-user
if not is_model_registered('user', 'User'):
    class User(User):
        history = HistoricalRecords(inherit=True)

        class Meta(User.Meta):
            pass

    __all__.append('User')


if not is_model_registered('user', 'Profile'):
    class Profile(AbstractProfile):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractProfile.Meta):
            pass

    __all__.append('Profile')
