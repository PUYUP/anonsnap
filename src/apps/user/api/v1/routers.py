from django.urls import path, include

from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .user.views import TokenObtainPairViewExtend, UserViewSet
from .password.views import PasswordResetView, PasswordResetConfirmView

router = DefaultRouter(trailing_slash=True)
router.register('users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairViewExtend.as_view(), name='token-obtain'),
    path('token-refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('reset-password/', PasswordResetView.as_view(),
         name='reset-password'),
    path('reset-password-confirm/', PasswordResetConfirmView.as_view(),
         name='reset-password-confirm'),
]
