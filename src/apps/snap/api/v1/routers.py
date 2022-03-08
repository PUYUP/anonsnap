from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .moment.views import MomentViewSet
from .attachment.views import AttachmentViewSet
from .comment.views import CommentViewSet
from .location.views import LocationViewSet
from .tag.views import MomentTagListView

router = DefaultRouter(trailing_slash=True)
router.register('moments', MomentViewSet, basename='moment')
router.register('attachments', AttachmentViewSet, basename='attachment')
router.register('comments', CommentViewSet, basename='comment')
router.register('locations', LocationViewSet, basename='location')

urlpatterns = [
    path('', include(router.urls)),
    path('tags/', MomentTagListView.as_view(), name='tag-list'),
]
