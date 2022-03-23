from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class ThrottleViewSet(object):
    def get_throttles(self):
        super().get_throttles()

        throttle_classes = (AnonRateThrottle, UserRateThrottle, )
        if self.action in ['list', 'retrieve']:
            throttle_classes = list()

        return [throttle() for throttle in throttle_classes]
