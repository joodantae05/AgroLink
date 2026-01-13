from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ReadingViewSet, TelemetryIngestView

router = DefaultRouter()
router.register(r'readings', ReadingViewSet, basename='readings')

urlpatterns = [
    path('', include(router.urls)),
    path('devices/<uuid:device_id>/telemetry', TelemetryIngestView.as_view()),
]
