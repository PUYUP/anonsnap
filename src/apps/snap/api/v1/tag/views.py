from django.apps import apps
from django.db.models import Count
from django.core.exceptions import FieldError
from django.utils.encoding import smart_str

from rest_framework import status as response_status
from rest_framework.viewsets import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import ListTagSerializer

Tag = apps.get_registered_model('taggit', 'Tag')
Moment = apps.get_registered_model('snap', 'Moment')
Attachment = apps.get_registered_model('snap', 'Attachment')


class MomentTagListView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = ListTagSerializer
    permission_classes = (AllowAny, )

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except FieldError as e:
            return Response(
                smart_str(e),
                status=response_status.HTTP_403_FORBIDDEN
            )

    def get_queryset(self):
        source = self.request.query_params.get('source')
        qs = self.queryset

        if source:
            qs_filter = {'{}__isnull'.format(source): False}
            qs = qs.filter(**qs_filter) \
                .annotate(count=Count(source)) \
                .order_by('-count') \
                .distinct()
        else:
            qs = qs.annotate(count=Count('taggit_taggeditem_items'))

        return qs
