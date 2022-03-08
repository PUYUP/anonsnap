from django.urls import path, include

from api.views import RootAPIView
from apps.user.api import routers as user_routers
from apps.core.api import routers as core_routers
from apps.snap.api import routers as snap_routers

urlpatterns = [
    path('', RootAPIView.as_view(), name='api'),
    path('', include(core_routers)),
    path('', include(user_routers)),
    path('', include(snap_routers)),
]
