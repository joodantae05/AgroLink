from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Device
from .serializers import DeviceCreateSerializer, DeviceSerializer


class DeviceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Device.objects.filter(owner=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return DeviceCreateSerializer
        return DeviceSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class DeviceRotateKeyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        device = get_object_or_404(Device, pk=pk, owner=request.user)
        raw = device.rotate_api_key()
        device.save(update_fields=['api_key_hash', 'api_key_prefix'])
        return Response({'api_key': raw}, status=status.HTTP_200_OK)
