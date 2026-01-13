from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DeviceRotateKeyView, DeviceViewSet

router = DefaultRouter()
router.register(r'devices', DeviceViewSet, basename='devices')

urlpatterns = [
    path('', include(router.urls)),
    path('devices/<uuid:pk>/rotate-key', DeviceRotateKeyView.as_view()),
]
