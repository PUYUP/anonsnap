from copy import copy

from django.db import transaction
from django.utils.encoding import smart_str
from django.apps import apps
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, OuterRef, Subquery, Exists
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
    ObjectDoesNotExist
)

from rest_framework import viewsets, status as response_status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.pagination import LimitOffsetPagination

from eav.queryset import EavQuerySet
from eav.models import Value, Attribute, Entity

from ..permissions import IsMomentOwnerOrReject
from ..utils import ThrottleViewSet
from .serializers import (
    CreateCommentSerializer,
    ListCommentSerializer,
    RetrieveCommentSerializer,
    UpdateCommentSerializer
)

PAGINATOR = LimitOffsetPagination()
Comment = apps.get_registered_model('snap', 'Comment')


class CommentViewSet(viewsets.ViewSet, ThrottleViewSet):
    """
    POST
    -------

        {
            "content_type": "<string>",
            "object_id": "<string>",
            "comment_content": ["<guid>"],
            "parent": "<guid>"
        }


    GET
    -------

        {
            "content_type": "<string>"
        }

    """
    lookup_field = 'guid'
    permission_classes = (AllowAny, )
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

    def initialize_request(self, request, *args, **kwargs):
        self.context.update({'request': request})
        return super().initialize_request(request, *args, **kwargs)

    def queryset(self):
        return Comment.objects \
            .prefetch_related('user', 'child', 'child__parent') \
            .select_related('user', 'content_type', 'child')

    def get_instance(self, guid, is_update=False):
        try:
            if is_update:
                return self.queryset().select_for_update().get(guid=guid)
            return self.queryset().get(guid=guid)
        except ObjectDoesNotExist:
            raise NotFound(detail=_("Moment not found"))

    def list(self, request):
        ct = request.query_params.get('content_type')
        queryset = self.queryset().filter(
            content_type__model=ct,
            content_type__app_label=Comment._meta.app_label
        )

        paginate_queryset = PAGINATOR.paginate_queryset(queryset, request)
        serializer = ListCommentSerializer(
            paginate_queryset,
            context=self.context,
            many=True
        )
        return PAGINATOR.get_paginated_response(serializer.data)

    def retrieve(self, request, guid=None):
        try:
            queryset = self.get_instance(guid)
        except ObjectDoesNotExist:
            return NotFound(detail=_("Comment not found"))
        except Exception as e:
            raise ValidationError(detail=smart_str(e))

        """
        d = queryset._meta.model.objects \
            .prefetch_related('user', 'content_type', 'child') \
            .select_related('user', 'content_type', 'child') \
            .filter(
                Q(eav__device_uuid='7250250292A') &
                Q(eav__device_imei='1052-525A') &
                Q(eav__device_iccid='I82522A') &
                Q(eav__device_imsi='089259252A')
            )
        

        d = queryset._meta.model.objects \
            .prefetch_related('user', 'content_type', 'child') \
            .select_related('user', 'content_type', 'child') \
            .filter(Q(eav__device_uuid='7250250292A')) \
            .filter(Q(eav__device_imei='1052-525A'))

        print(d)
        """

        """
        v = Value.objects \
            .prefetch_related('entity_ct', 'attribute', 'value_enum', 'generic_value_ct') \
            .select_related('entity_ct', 'attribute', 'value_enum', 'generic_value_ct') \
            .all()
        print(v)
        

        t = queryset.eav_values \
            .prefetch_related('attribute', 'entity_ct') \
            .select_related('attribute', 'entity_ct') \
            .filter(
                Q(attribute__slug='device_uuid', value_text='7250250292A') |
                Q(attribute__slug='device_imei', value_text='1052-525Ax'),
                Q(entity_id=queryset.id)
            )
        print(t)
        

        v = Value.objects.filter(
            entity_id=queryset.id,
            value_text__in=['1052-525A', '7250250292Ad'],
            attribute__slug__in=['device_imei', 'device_uuid']
        )
        print(v)
        

        q1 = Q(eav__device_uuid='7250250292A')
        q2 = Q(eav__device_imei='1052-525A')
        q3 = Q(eav__device_imsi='089259252A')
        q4 = Q(eav__device_iccid='I82522A')
        r = Comment.objects.filter(
            (q1 & q2) & (q3 & q4)
        )
        print(r)
        """

        attributes = [
            {"slug": "device_imei", "value_text": "1052-525A"},
            {"slug": "device_iccid", "value_text": "I82522A"},
            {"slug": "device_imsi", "value_text": "089259252A"},
            {"slug": "device_uuid", "value_text": "7250250292A"}
        ]

        """
        valued = list()
        for attr in attributes:
            k = {
                'attribute__{}'.format(k)
                if k == 'slug' else k: v for k, v in attr.items()
            }

            vo = Value.objects \
                .filter(entity_id=OuterRef('entity_id'), **k)

        sq = Value.objects.filter(entity_id=OuterRef('entity_id')) \
            .extra(where=["attribute_id='126' AND value_text='1052-525A'", "attribute_id='127' AND value_text='089259252A'"])

        y = queryset.eav_values \
            .prefetch_related('attribute') \
            .select_related('attribute') \
            .annotate(tq=Exists(sq)) \
            .filter(tq=True)

        print(y.query)
        """

        pq = queryset._meta.model.objects.filter(
            eav_values__attribute__slug__startswith='device'
        ).distinct().get(id=queryset.id)

        w = Entity(pq)

        print(w.get_values_dict())

        serializer = RetrieveCommentSerializer(
            instance=queryset,
            context=self.context
        )
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @transaction.atomic
    def create(self, request):
        serializer = CreateCommentSerializer(
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
        serializer = UpdateCommentSerializer(
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
        serializer = RetrieveCommentSerializer(
            instance_copy,
            context=self.context
        )

        return Response(
            serializer.data,
            status=response_status.HTTP_202_ACCEPTED
        )
