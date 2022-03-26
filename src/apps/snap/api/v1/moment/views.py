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
from django.db.models.expressions import OuterRef, Subquery, Exists
from django.db.models import F, Value, FloatField, Count, Case, When, Prefetch, Q
from django.contrib.contenttypes.models import ContentType

from rest_framework import viewsets, status as response_status
from rest_framework.permissions import AllowAny, IsAuthenticated
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
from ..permissions import IsOwnerOrReject

PAGINATOR = LimitOffsetPagination()

Location = apps.get_registered_model('snap', 'Location')
Moment = apps.get_registered_model('snap', 'Moment')
Comment = apps.get_registered_model('snap', 'Comment')
Reaction = apps.get_registered_model('snap', 'Reaction')
Attachment = apps.get_registered_model('snap', 'Attachment')


class MomentViewSet(ThrottleViewSet, viewsets.ViewSet):
    """
    POST
    -------

        {
            "title": "<string> [required]",
            "summary": "<string>",
            "locations": ["<guid>"],
            "attachments": ["<guid>"],
        }


    GET
    -------

        {
            "latitude": "<float>",
            "longitude": "<float>",
            "user_latitude": "<float>",
            "user_longitude": "<float>",
            "radius": "<number>",
            "tag": "<string>",
            "byme": "<number 0 or 1>"
        }

    """
    lookup_field = 'guid'
    permission_classes = (AllowAny,)
    permission_action = {
        'create': (IsAuthenticated,),
        'partial_update': (IsOwnerOrReject,),
        'destroy': (IsOwnerOrReject,),
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
        """Get moment by coordinate in map
        and calculate distance from user real location"""

        # taken from map
        latitude = self.request.query_params.get('latitude')
        longitude = self.request.query_params.get('longitude')
        radius = self.request.query_params.get('radius', 5)  # in kilometer

        # actual user coordinate
        user_latitude = self.request.query_params.get('user_latitude')
        user_longitude = self.request.query_params.get('user_longitude')

        if latitude and longitude:
            # moment by location selected in map
            # in kilometer use: 6371, in miles use: 3959
            calculate_distance = Value(6371) * ACos(
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

            location = Location.objects \
                .filter(
                    object_id=OuterRef('id'),
                    content_type__model=Moment._meta.model_name) \
                .annotate(distance=calculate_distance)

            queryset = queryset.annotate(
                distance=Subquery(location.values('distance')[:1]))

            # calculate user distance from moment
            if user_latitude and user_longitude:
                calculate_user_distance = Value(6371) * ACos(
                    Cos(Radians(float(user_latitude), output_field=FloatField()))
                    * Cos(Radians(F('latitude'), output_field=FloatField()))
                    * Cos(
                        Radians(F('longitude'), output_field=FloatField())
                        - Radians(float(user_longitude),
                                  output_field=FloatField())
                    )
                    + Sin(Radians(float(user_latitude), output_field=FloatField()))
                    * Sin(Radians(F('latitude'), output_field=FloatField())),
                    output_field=FloatField()
                )

                location = location.annotate(user_distance=calculate_user_distance)
                queryset = queryset \
                    .annotate(user_distance=Subquery(location.values('user_distance')[:1])) \
                    .order_by('user_distance')

            else:
                queryset = queryset.order_by('-create_at')

            # not by me!
            # show moment from all users
            # but make sure moment has location!
            if self.request.query_params.get('byme', '0') != '1':
                queryset = queryset \
                    .filter(Q(distance__isnull=False) & Q(distance__lte=radius))

        return queryset

    def _querying_date(self, queryset):
        fromdate = self.request.query_params.get('fromdate')
        todate = self.request.query_params.get('todate')
        somedate = fromdate or todate  # return None if two date None

        if fromdate and todate:
            queryset = queryset.filter(
                create_at__gte=fromdate,
                create_at__lte=todate)

        elif somedate:
            queryset = queryset.filter(create_at__date=somedate)

        return queryset

    def _querying_tag(self, queryset):
        # can separate with comma
        tag = self.request.query_params.get('tag')
        if tag:
            tags = tag.split(',')
            taglist = [t.strip() for t in tags]
            queryset = queryset.filter(tags__name__in=taglist).distinct()
        return queryset

    def initialize_request(self, request, *args, **kwargs):
        self.context.update({'request': request})
        return super().initialize_request(request, *args, **kwargs)

    def queryset(self):
        user = self.request.user
        content_type = ContentType.objects.get_for_model(Moment._meta.model)
        reaction = Reaction.objects \
            .filter(
                object_id=OuterRef('id'),
                content_type=content_type.id,
                user_id=user.id
            )

        return Moment.objects \
            .prefetch_related(
                'user',
                Prefetch(
                    'attachments',
                    queryset=Attachment.objects.order_by('-create_at')
                ),
                'attachments__locations',
                'locations',
                Prefetch(
                    'reactions',
                    queryset=Reaction.objects.filter(user_id=user.id)
                ),
                'reactions__content_object',
                'tags',
                'withs'
            ) \
            .select_related('user') \
            .annotate(
                comment_count=Count('comments', distinct=True),
                reaction_count=Count('reactions', distinct=True),
                is_owner=Case(
                    When(
                        Q(user__isnull=False) & Q(user_id=user.id),
                        then=Value(True)
                    ),
                    default=Value(False)
                )
            )

    def get_instance(self, guid, is_update=False):
        try:
            if is_update:
                return self.queryset().select_for_update().get(guid=guid)
            return self.queryset().get(guid=guid)
        except ObjectDoesNotExist:
            raise NotFound(detail=_("Moment not found"))

    def list(self, request):
        queryset = self._querying_distance(self.queryset())
        queryset = self._querying_tag(queryset)
        queryset = self._querying_date(queryset)

        if request.query_params.get('byme', '0') == '1':
            queryset = queryset.filter(user_id=request.user.id)

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
