from django.urls import path, include
from apps.user.api.v1 import routers

urlpatterns = [
    path('user/v1/', include((routers, 'user_api'), namespace='user_api')),
]
