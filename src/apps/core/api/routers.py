from django.urls import path, include
from .v1 import routers

urlpatterns = [
    path('core/v1/', include((routers, 'core_api'), namespace='core_api')),
]
