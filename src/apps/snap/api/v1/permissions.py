import json

from django.db.models import Q
from rest_framework import permissions


class IsMomentOwnerOrReject(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # todo permission by attribute
        if request.user.is_authenticated and hasattr(obj.user, 'id'):
            return obj.user.id == request.user.id
        else:
            attributes = request.data.get('attributes')
            if not attributes and request.method == 'DELETE':
                body_unicode = request.body.decode('utf-8')
                if body_unicode:
                    body = json.loads(body_unicode)
                    attributes = body.get('attributes')

            if not attributes:
                return False

            attr_q = Q()
            for attr in attributes:
                slug = attr.get('slug')
                key = 'eav__{}'.format(slug)
                attr_q &= Q(**{
                    key: v for k, v in attr.items()
                })

            if not attr_q:
                return False

            return obj.eav_values \
                .prefetch_related('attribute') \
                .select_related('attribute') \
                .exists()
