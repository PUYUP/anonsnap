from django.apps import apps
from django.db.models import Count
from django.core.exceptions import FieldError
from django.utils.encoding import smart_str
from django.db.models.functions import ACos, Cos, Sin, Radians
from django.db.models import F, Value, FloatField, OuterRef, Subquery, Avg

from rest_framework import status as response_status
from rest_framework.viewsets import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from taggit.models import Tag
from .serializers import ListTagSerializer

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
        max_radius = 5000000
        latitude = self.request.query_params.get('latitude')
        longitude = self.request.query_params.get('longitude')

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

        if latitude and longitude:
            # calculate distance based on current user location
            # by their latitude and longitude
            # in kilometer use: 6371, in miles use: 3959
            calculate_distance = Value(6371) * ACos(
                Cos(Radians(float(latitude), output_field=FloatField()))
                * Cos(
                    Radians(
                        F('locations__latitude'), output_field=FloatField()
                    )
                )
                * Cos(
                    Radians(
                        F('locations__longitude'), output_field=FloatField()
                    ) - Radians(float(longitude), output_field=FloatField())
                )
                + Sin(Radians(float(latitude), output_field=FloatField()))
                * Sin(
                    Radians(
                        F('locations__latitude'), output_field=FloatField()
                    )
                ),
                output_field=FloatField()
            )

            instance_subquery = Moment.objects.filter(
                id=OuterRef('taggit_taggeditem_items__id')
            ).annotate(distance=calculate_distance)

            qs = qs.annotate(
                distance=Avg(Subquery(instance_subquery.values('distance')))
            ).filter(distance__lte=max_radius)

        return qs
