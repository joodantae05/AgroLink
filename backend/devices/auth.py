from django.contrib.auth.hashers import check_password
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import Device


class DeviceUser:
    def __init__(self, device):
        self.device = device
        self.is_authenticated = True
        self.id = device.id


class DeviceAPIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        raw_key = request.headers.get('X-API-Key')
        if not raw_key:
            return None

        prefix = raw_key[:8]
        device = Device.objects.filter(api_key_prefix=prefix).first()
        if not device or not check_password(raw_key, device.api_key_hash):
            raise AuthenticationFailed('Invalid device api key')

        request.device = device
        return (DeviceUser(device), None)
