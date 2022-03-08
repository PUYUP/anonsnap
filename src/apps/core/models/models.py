from apps.core.utils import is_model_registered
from simple_history.models import HistoricalRecords

from .verification import *

__all__ = list()


if not is_model_registered('core', 'Verification'):
    class Verification(AbstractVerification):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractVerification.Meta):
            pass

    __all__.append('Verification')
