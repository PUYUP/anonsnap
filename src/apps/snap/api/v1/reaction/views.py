from copy import copy

from django.db import transaction
from django.utils.encoding import smart_str
from django.apps import apps
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
    ObjectDoesNotExist
)

from rest_framework import viewsets, status as response_status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound

from ..permissions import IsOwnerOrReject
from ..utils import ThrottleViewSet
from .serializers import (CreateReactionSerializer, RetrieveReactionSerializer)

Reaction = apps.get_registered_model('snap', 'Reaction')


class ReactionViewSet(ThrottleViewSet, viewsets.ViewSet):
    """
    POST
    -------

        {
            "content_type": "<string>",
            "object_id": "<string>",
            "identifier": "<string>"
        }
    """
    lookup_field = 'guid'
    permission_classes = (AllowAny, )
    permission_action = {
        'create': (IsAuthenticated,),
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

    def initialize_request(self, request, *args, **kwargs):
        self.context.update({'request': request})
        return super().initialize_request(request, *args, **kwargs)

    def queryset(self):
        return Reaction.objects \
            .prefetch_related('user', 'content_object') \
            .select_related('user', 'content_type')

    def get_instance(self, guid, is_update=False):
        try:
            if is_update:
                return self.queryset().select_for_update().get(guid=guid)
            return self.queryset().get(guid=guid)
        except ObjectDoesNotExist:
            raise NotFound(detail=_("Not found"))

    def list(self, request):
        return Response('OK', status=response_status.HTTP_200_OK)

    @transaction.atomic
    def create(self, request):
        serializer = CreateReactionSerializer(
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
    def destroy(self, request, guid=None):
        instance = self.get_instance(guid, is_update=True)
        self.check_object_permissions(request, instance)

        # copy for response
        instance_copy = copy(instance)

        # run delete
        instance.delete()

        # return object
        serializer = RetrieveReactionSerializer(
            instance_copy,
            context=self.context
        )

        return Response(
            serializer.data,
            status=response_status.HTTP_202_ACCEPTED
        )
