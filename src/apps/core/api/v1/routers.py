from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .verification.views import VerificationViewSet

router = DefaultRouter(trailing_slash=True)
router.register('verifications', VerificationViewSet, basename='verification')

urlpatterns = [
    path('', include(router.urls)),
]
