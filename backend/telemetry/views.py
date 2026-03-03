from uuid import UUID

from django.utils import timezone as dj_timezone
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.constants import SENSOR_CATALOG, SENSOR_TYPES, SENSOR_UNITS
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
            unit = (item.get('unit') or '').strip().lower()
            if sensor_type is None or value is None or sensor_type not in allowed_sensor_types:
                continue

            expected_unit = SENSOR_UNITS.get(sensor_type, '')
            if unit and expected_unit and unit != expected_unit:
                continue

            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                continue

            rows.append(
                Reading(
                    device=device,
                    sensor_type=sensor_type,
                    value=numeric_value,
                    unit=expected_unit or unit,
                    measured_at=ts,
                )
            )

        if rows:
            Reading.objects.bulk_create(rows)
            device.last_seen_at = dj_timezone.now()
            device.save(update_fields=['last_seen_at'])

        return Response({'ingested': len(rows)}, status=status.HTTP_201_CREATED)


class SensorCatalogView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'sensors': SENSOR_CATALOG}, status=status.HTTP_200_OK)


class LatestReadingsSnapshotView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        requested_device_id = request.query_params.get('device_id')
        readings_qs = Reading.objects.order_by('-measured_at', '-created_at')

        if requested_device_id:
            try:
                parsed_device_id = UUID(str(requested_device_id))
            except (TypeError, ValueError):
                return Response({'detail': 'Invalid device_id'}, status=status.HTTP_400_BAD_REQUEST)
            readings_qs = readings_qs.filter(device_id=parsed_device_id)

        latest_row = readings_qs.first()
        if not latest_row:
            return Response(
                {
                    'device_id': str(requested_device_id) if requested_device_id else None,
                    'measured_at': None,
                    'readings': [],
                },
                status=status.HTTP_200_OK,
            )

        target_device_id = str(latest_row.device_id)
        sensor_types = [sensor['type'] for sensor in SENSOR_CATALOG]

        rows = (
            Reading.objects.filter(device_id=target_device_id, sensor_type__in=sensor_types)
            .order_by('-measured_at', '-created_at')
        )

        latest_by_type = {}
        for row in rows:
            if row.sensor_type not in latest_by_type:
                latest_by_type[row.sensor_type] = row
            if len(latest_by_type) == len(sensor_types):
                break

        response_rows = []
        measured_at = None
        for sensor in SENSOR_CATALOG:
            sensor_type = sensor['type']
            row = latest_by_type.get(sensor_type)
            if not row:
                continue

            if measured_at is None or row.measured_at > measured_at:
                measured_at = row.measured_at

            response_rows.append(
                {
                    'type': sensor_type,
                    'label': sensor['label'],
                    'unit': sensor['unit'],
                    'value': row.value,
                    'measured_at': row.measured_at.isoformat(),
                }
            )

        return Response(
            {
                'device_id': target_device_id,
                'measured_at': measured_at.isoformat() if measured_at else None,
                'readings': response_rows,
            },
            status=status.HTTP_200_OK,
        )


class ReadingViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ReadingSerializer

    def get_queryset(self):
        qs = Reading.objects.filter(device__owner=self.request.user).order_by('-measured_at')
        device_id = self.request.query_params.get('device_id')
        if device_id:
            try:
                UUID(str(device_id))
            except (TypeError, ValueError):
                return qs.none()
            qs = qs.filter(device_id=device_id)
        return qs
