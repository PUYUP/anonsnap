from django.urls import path, include
from .v1 import routers

urlpatterns = [
    path('snap/v1/', include((routers, 'snap_api'), namespace='snap_api')),
]
