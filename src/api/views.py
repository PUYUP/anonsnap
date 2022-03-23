from django.utils.translation import gettext_lazy as _

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.permissions import AllowAny


class RootAPIView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        return Response({
            'user': {
                'user': reverse('user_api:user-list', request=request,
                                format=format, current_app='user'),
                'token': reverse('user_api:token-obtain', request=request,
                                 format=format, current_app='user'),
                'reset-password': reverse('user_api:reset-password',
                                          request=request,
                                          format=format, current_app='user'),
                'reset-password-confirm': reverse(
                    'user_api:reset-password-confirm',
                    request=request,
                    format=format,
                    current_app='user'
                ),
            },
            'core': {
                'verification': reverse('core_api:verification-list',
                                        request=request, format=format,
                                        current_app='core'),
            },
            'snap': {
                'moment': reverse('snap_api:moment-list',
                                  request=request, format=format,
                                  current_app='snap'),
                'attachment': reverse('snap_api:attachment-list',
                                      request=request, format=format,
                                      current_app='snap'),
                'location': reverse('snap_api:location-list',
                                    request=request, format=format,
                                    current_app='snap'),
                'tag': reverse('snap_api:tag-list',
                               request=request, format=format,
                               current_app='snap'),
                'comment': reverse('snap_api:comment-list',
                                   request=request, format=format,
                                   current_app='snap'),
                'reaction': reverse('snap_api:reaction-list',
                                    request=request, format=format,
                                    current_app='snap'),
            },
        })
