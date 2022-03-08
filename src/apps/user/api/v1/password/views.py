from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils.encoding import smart_str

from rest_framework import status as response_status
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from rest_framework.response import Response

from .serializers import (
    PasswordResetSerializer,
    SerializerPasswordResetConfirm
)


class PasswordResetView(APIView):
    """
    POST
    ------

        {
            "resetwith": "email or msisdn",
            "value": "string"
        }
    """
    permission_classes = (AllowAny,)
    throttle_classes = (AnonRateThrottle,)

    @transaction.atomic
    def post(self, request):
        serializer = PasswordResetSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except DjangoValidationError as e:
                raise ValidationError(smart_str(e))
            return Response(
                serializer.data,
                status=response_status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=response_status.HTTP_403_FORBIDDEN
        )


class PasswordResetConfirmView(APIView):
    """
    POST
    ------

        {
            "uid": "string",
            "reset_token": "string",
            "resetwith": "email or msisdn",
            "passcode": "string",
            "verification_token": "string",
            "new_password": "string",
            "retype_password": "string"
        }
    """
    permission_classes = (AllowAny,)
    throttle_classes = (AnonRateThrottle,)

    @transaction.atomic
    def post(self, request):
        serializer = SerializerPasswordResetConfirm(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except DjangoValidationError as e:
                raise ValidationError(smart_str(e))
            return Response(
                serializer.data,
                status=response_status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=response_status.HTTP_403_FORBIDDEN
        )
