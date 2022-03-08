from django.db import transaction
from django.utils.encoding import smart_str
from django.core.exceptions import (
    ValidationError as DjangoValidationError
)
from django.apps import apps

from rest_framework import viewsets, status as response_status
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .serializers import (
    CreateVerificationSerializer,
    ValidateVerificationSerializer
)

Verification = apps.get_registered_model('core', 'Verification')
User = apps.get_registered_model('user', 'User')


class BaseViewSet(viewsets.ViewSet):
    lookup_field = 'passcode'
    permission_classes = [AllowAny, ]
    throttle_classes = (AnonRateThrottle,)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.context = dict()

    def initialize_request(self, request, *args, **kwargs):
        self.context.update({'request': request})
        return super().initialize_request(request, *args, **kwargs)


class VerificationViewSet(BaseViewSet):
    """
    POST
    -----

        {
            "content_type": "model name",
            "field": "model field",
            "value": "model field value",
            "challenge": "obtain for?",
            "sendwith": "msisdn,email",
            "sendto": "email address or phone number"
        }


    UPDATE (Validation)
    ------

        {
            "challenge": "msisdn_verification",
            "token": "md5"
        }
    """
    @transaction.atomic
    def create(self, request):
        serializer = CreateVerificationSerializer(
            data=request.data,
            context=self.context
        )

        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except DjangoValidationError as e:
                raise ValidationError(detail=smart_str(e))
            return Response(
                serializer.data,
                status=response_status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=response_status.HTTP_406_NOT_ACCEPTABLE
        )

    @transaction.atomic
    def partial_update(self, request, passcode=None):
        instances = Verification.objects \
            .select_for_update() \
            .filter(passcode=passcode)

        serializer = ValidateVerificationSerializer(
            instances,
            data=request.data,
            context=self.context,
            partial=True
        )

        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except DjangoValidationError as e:
                raise ValidationError(detail=smart_str(e))
            return Response(
                serializer.data,
                status=response_status.HTTP_202_ACCEPTED
            )
        return Response(
            serializer.errors,
            status=response_status.HTTP_406_NOT_ACCEPTABLE
        )

    def retrieve(self, request, passcode=None):
        return Response(status=response_status.HTTP_200_OK)
