from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_str

from rest_framework import serializers
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class ThrottleViewSet(object):
    def get_throttles(self):
        super().get_throttles()

        if self.action in ['create', 'partial_update', 'destroy']:
            throttle_classes = (AnonRateThrottle, UserRateThrottle, )
        else:
            throttle_classes = []
        return [throttle() for throttle in throttle_classes]
