from django.apps import apps
from django.db.models import Count
from django.core.exceptions import FieldError
from django.utils.encoding import smart_str
from django.db.models.functions import ACos, Cos, Sin, Radians
from django.db.models import F, Value, FloatField, OuterRef, Subquery, Avg, Q

from rest_framework import status as response_status
from rest_framework.viewsets import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from taggit.models import Tag
from .serializers import ListTagSerializer

Moment = apps.get_registered_model('snap', 'Moment')
Attachment = apps.get_registered_model('snap', 'Attachment')
Location = apps.get_registered_model('snap', 'Location')


class MomentTagListView(generics.ListAPIView):
    """
    GET
    ------
    
        {
            "latitude": "<float>",
            "longitude": "<float>",
            "user_latitude": "<float>",
            "user_longitude": "<float>",
            "radius": "<number>",
            "content_type": "<string>"
        }
    """
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
        # taken from map
        latitude = self.request.query_params.get('latitude')
        longitude = self.request.query_params.get('longitude')
        radius = self.request.query_params.get('radius', 5)  # in kilometer

        # actual user coordinate
        user_latitude = self.request.query_params.get('user_latitude')
        user_longitude = self.request.query_params.get('user_longitude')

        content_type = self.request.query_params.get('content_type')
        qs = self.queryset

        if content_type:
            qs_filter = {'{}__isnull'.format(content_type): False}
            qs = qs.filter(**qs_filter) \
                .annotate(count=Count(content_type)) \
                .order_by('-count') \
                .distinct()
        else:
            qs = qs.annotate(
                count=Count('taggit_taggeditem_items', distinct=True))

        if latitude and longitude:
            # calculate distance based on current user location
            # by their latitude and longitude
            # in kilometer use: 6371, in miles use: 3959
            calculate_distance = Value(6371) * ACos(
                Cos(Radians(float(latitude), output_field=FloatField()))
                * Cos(Radians(F('latitude'), output_field=FloatField()))
                * Cos(
                    Radians(
                        F('longitude'), output_field=FloatField()
                    ) - Radians(float(longitude), output_field=FloatField())
                )
                + Sin(Radians(float(latitude), output_field=FloatField()))
                * Sin(Radians(F('latitude'), output_field=FloatField())),
                output_field=FloatField()
            )

            location = Location.objects \
                .filter(
                    object_id=OuterRef('id'),
                    content_type__model=Moment._meta.model_name
                ).annotate(distance=calculate_distance)

            moment = Moment.objects \
                .filter(id=OuterRef('taggit_taggeditem_items__object_id')) \
                .annotate(distance=Subquery(location.values('distance')[:1]))

            if radius:
                moment = moment.filter(
                    Q(distance__isnull=False) & Q(distance__lte=radius))

            # calculate user distance from tag
            if user_latitude and user_longitude:
                calculate_user_distance = Value(6371) * ACos(
                    Cos(Radians(float(user_latitude), output_field=FloatField()))
                    * Cos(Radians(F('latitude'), output_field=FloatField()))
                    * Cos(
                        Radians(
                            F('longitude'), output_field=FloatField()
                        ) - Radians(float(user_longitude), output_field=FloatField())
                    )
                    + Sin(Radians(float(user_latitude), output_field=FloatField()))
                    * Sin(Radians(F('latitude'), output_field=FloatField())),
                    output_field=FloatField()
                )

                location = location.annotate(
                    user_distance=calculate_user_distance)

                moment = moment.annotate(
                    user_distance=Subquery(location.values('user_distance')[:1]))

                qs = qs.annotate(
                    user_distance=Avg(Subquery(moment.values('user_distance'))))
            qs = qs.annotate(distance=Avg(Subquery(moment.values('distance'))))

            return qs.filter(Q(distance__isnull=False) & Q(distance__lte=radius)) \
                .order_by('distance')
        return qs
