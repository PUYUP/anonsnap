from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import viewsets, status as response_status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny

from .serializers import CreateAttachmentSerializer
from ..utils import ThrottleViewSet


class AttachmentViewSet(viewsets.ViewSet, ThrottleViewSet):
    """
    POST
    ------
    
        {
            "file": "<file>",
            "locations": ["<guid>"]
        }

    """
    lookup_field = 'guid'
    parser_classes = (MultiPartParser,)
    permission_classes = (AllowAny,)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.context = dict()

    def initialize_request(self, request, *args, **kwargs):
        self.context.update({'request': request})
        return super().initialize_request(request, *args, **kwargs)

    def list(self, request):
        return Response(status=response_status.HTTP_200_OK)

    @transaction.atomic
    def create(self, request):
        serializer = CreateAttachmentSerializer(
            data=request.data,
            context=self.context
        )

        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except DjangoValidationError as e:
                raise ValidationError(detail=str(e))
            return Response(
                serializer.data,
                status=response_status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=response_status.HTTP_406_NOT_ACCEPTABLE
        )
