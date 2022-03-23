from copy import copy

from django.db import transaction
from django.utils.encoding import smart_str
from django.apps import apps
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
    ObjectDoesNotExist
)
from django.db.models import Value, Case, When

from rest_framework import viewsets, status as response_status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.pagination import LimitOffsetPagination

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


class CommentViewSet(ThrottleViewSet, viewsets.ViewSet):
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
            "content_type": "<string>",
            "object_id": "<uuid 4>",
            "byme": "<number 0 or 1>"
        }

    """
    lookup_field = 'guid'
    permission_classes = (AllowAny, )
    permission_action = {
        'create': (IsAuthenticated,),
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
        user = self.request.user

        return Comment.objects \
            .prefetch_related('user', 'child', 'child__parent', 'content_object') \
            .select_related('user', 'content_type', 'child') \
            .annotate(
                is_owner=Case(
                    When(user_id=user.id, then=Value(True)),
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
        if request.query_params.get('byme', '0') == '1':
            queryset = self.queryset().filter(user_id=request.user.id)
        else:
            ct = request.query_params.get('content_type')
            object_id = request.query_params.get('object_id')

            queryset = self.queryset().filter(
                content_type__model=ct,
                content_type__app_label=Comment._meta.app_label,
                moment__guid=object_id
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
