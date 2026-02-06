from django.utils import timezone as dj_timezone
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.constants import SENSOR_TYPES
from common.utils import parse_iso8601
from devices.auth import DeviceAPIKeyAuthentication
from .models import Reading
from .serializers import ReadingSerializer


class IsDeviceAuthenticated:
    def has_permission(self, request, view):
        return hasattr(request, 'device')


class TelemetryIngestView(APIView):
    authentication_classes = [DeviceAPIKeyAuthentication]
    permission_classes = [IsDeviceAuthenticated]

    def post(self, request, device_id):
        device = getattr(request, 'device', None)
        if not device or str(device.id) != str(device_id):
            return Response({'detail': 'Device mismatch'}, status=status.HTTP_403_FORBIDDEN)

        payload = request.data or {}
        ts = parse_iso8601(payload.get('ts')) or dj_timezone.now()
        readings = payload.get('readings') or []
        allowed_sensor_types = {sensor[0] for sensor in SENSOR_TYPES}

        rows = []
        for item in readings:
            sensor_type = item.get('type')
            value = item.get('value')
            unit = item.get('unit') or ''
            if sensor_type is None or value is None or sensor_type not in allowed_sensor_types:
                continue
            rows.append(Reading(device=device, sensor_type=sensor_type, value=value, unit=unit, measured_at=ts))

        if rows:
            Reading.objects.bulk_create(rows)
            device.last_seen_at = dj_timezone.now()
            device.save(update_fields=['last_seen_at'])

        return Response({'ingested': len(rows)}, status=status.HTTP_201_CREATED)


class ReadingViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ReadingSerializer

    def get_queryset(self):
        qs = Reading.objects.filter(device__owner=self.request.user).order_by('-measured_at')
        device_id = self.request.query_params.get('device_id')
        if device_id:
            qs = qs.filter(device_id=device_id)
        return qs
