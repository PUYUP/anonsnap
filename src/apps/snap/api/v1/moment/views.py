from copy import copy

from django.db import transaction
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
    ObjectDoesNotExist
)
from django.utils.encoding import smart_str
from django.utils.translation import gettext_lazy as _
from django.apps import apps
from django.db.models.functions import ACos, Cos, Sin, Radians
from django.db.models.expressions import OuterRef, Subquery
from django.db.models import F, Value, FloatField

from rest_framework import viewsets, status as response_status
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from .serializers import (
    CreateMomentSerializer,
    UpdateMomentSerializer,
    ListMomentSerializer,
    RetrieveMomentSerializer
)
from ..utils import ThrottleViewSet
from ..permissions import IsMomentOwnerOrReject

USE_KILOMETER = 6371
USE_MILE = 3959
PAGINATOR = LimitOffsetPagination()

Location = apps.get_registered_model('snap', 'Location')
Moment = apps.get_registered_model('snap', 'Moment')


class MomentViewSet(viewsets.ViewSet, ThrottleViewSet):
    """
    POST
    -------

        {
            "title": "<string> [required]",
            "summary": "<string>",
            "locations": ["<guid>"],
            "attachments": ["<guid>"],
            "attributes": [
                {"slug": "device_iccid", "value_text": "<string>"},
                {"slug": "device_imei", "value_text": "<string>"},
                {"slug": "device_imsi", "value_text": "<string>"},
                {"slug": "device_uuid", "value_text": "<string>"}
            ]
        }

        Note:
        When update `attributes` only used for check anonym user
        owned their moment. Especially start with `device_<param>`


    GET
    -------

        {
            "radius": "in km <integer>"
        }

    """
    lookup_field = 'guid'
    permission_classes = (AllowAny,)
    permission_action = {
        'partial_update': (IsMomentOwnerOrReject,),
        'destroy': (IsMomentOwnerOrReject,),
    }

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.context = dict()

    def get_permissions(self):
        """
        Instantiates and returns
        the list of permissions that this view requires.
        """
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_action[self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]

    def _querying_distance(self, queryset):
        max_radius = 5000000
        request = self.request
        latitude = request.query_params.get('latitude')
        longitude = request.query_params.get('longitude')

        if latitude and longitude:
            # calculate distance based on current user location
            # by their latitude and longitude
            calculate_distance = Value(USE_KILOMETER) * ACos(
                Cos(Radians(float(latitude), output_field=FloatField()))
                * Cos(Radians(F('latitude'), output_field=FloatField()))
                * Cos(
                    Radians(F('longitude'), output_field=FloatField())
                    - Radians(float(longitude), output_field=FloatField())
                )
                + Sin(Radians(float(latitude), output_field=FloatField()))
                * Sin(Radians(F('latitude'), output_field=FloatField())),
                output_field=FloatField()
            )
            location = Location.objects.filter(
                object_id=OuterRef('id'),
                content_type__model=Moment._meta.model_name
            ).annotate(distance=calculate_distance)

            queryset = queryset.annotate(
                distance=Subquery(location.values('distance')[:1])
            ).filter(distance__lte=max_radius)

        return queryset

    def initialize_request(self, request, *args, **kwargs):
        self.context.update({'request': request})
        return super().initialize_request(request, *args, **kwargs)

    def queryset(self):
        return Moment.objects \
            .prefetch_related('user', 'attachments', 'attachments__locations',
                              'locations', 'tags', 'withs') \
            .select_related('user')

    def get_instance(self, guid, is_update=False):
        try:
            if is_update:
                return self.queryset().select_for_update().get(guid=guid)
            return self.queryset().get(guid=guid)
        except ObjectDoesNotExist:
            raise NotFound(detail=_("Moment not found"))

    def list(self, request):
        queryset = self._querying_distance(self.queryset())
        paginate_queryset = PAGINATOR.paginate_queryset(queryset, request)
        serializer = ListMomentSerializer(
            paginate_queryset,
            context=self.context,
            many=True
        )
        return PAGINATOR.get_paginated_response(serializer.data)

    def retrieve(self, request, guid=None):
        try:
            queryset = self._querying_distance(self.queryset()).get(guid=guid)
        except ObjectDoesNotExist:
            return NotFound(detail=_("Moment not found"))
        except Exception as e:
            raise ValidationError(detail=smart_str(e))

        serializer = RetrieveMomentSerializer(
            instance=queryset,
            context=self.context
        )
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @transaction.atomic
    def create(self, request):
        serializer = CreateMomentSerializer(
            data=request.data,
            context=self.context
        )
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except DjangoValidationError as e:
                raise ValidationError(smart_str(e))
            return Response(
                serializer.data,
                status=response_status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=response_status.HTTP_403_FORBIDDEN
        )

    @transaction.atomic
    def partial_update(self, request, guid=None):
        instance = self.get_instance(guid, is_update=True)
        self.check_object_permissions(request, instance)
        serializer = UpdateMomentSerializer(
            instance,
            data=request.data,
            context=self.context,
            partial=True
        )
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except DjangoValidationError as e:
                raise ValidationError(smart_str(e))
            return Response(
                serializer.data,
                status=response_status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=response_status.HTTP_403_FORBIDDEN
        )

    @transaction.atomic
    def destroy(self, request, guid=None):
        instance = self.get_instance(guid, is_update=True)
        self.check_object_permissions(request, instance)

        # copy for response
        instance_copy = copy(instance)

        # run delete
        instance.delete()

        # return object
        serializer = RetrieveMomentSerializer(
            instance_copy,
            context=self.context
        )

        return Response(
            serializer.data,
            status=response_status.HTTP_202_ACCEPTED
        )
