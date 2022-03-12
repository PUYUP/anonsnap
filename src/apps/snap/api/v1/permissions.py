import json

from django.db.models import Q
from rest_framework import permissions


class IsMomentOwnerOrReject(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # todo permission by attribute
        return obj.user.id == request.user.id
