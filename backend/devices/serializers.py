import re

from django.utils.html import strip_tags
from rest_framework import serializers

from .models import Device

DEVICE_NAME_PATTERN = re.compile(r'^[\w\s\-().#]{1,120}$')


def validate_device_name(value):
    name = (value or '').strip()
    if name != strip_tags(name):
        raise serializers.ValidationError('HTML tags are not allowed in device name.')
    if not DEVICE_NAME_PATTERN.match(name):
        raise serializers.ValidationError('Device name contains unsupported characters.')
    return name


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['id', 'name', 'status', 'last_seen_at', 'created_at']
        read_only_fields = ['id', 'last_seen_at', 'created_at']

    def validate_name(self, value):
        return validate_device_name(value)


class DeviceCreateSerializer(serializers.ModelSerializer):
    api_key = serializers.CharField(read_only=True)

    class Meta:
        model = Device
        fields = ['id', 'name', 'status', 'api_key', 'created_at']
        read_only_fields = ['id', 'api_key', 'created_at']

    def validate_name(self, value):
        return validate_device_name(value)

    def create(self, validated_data):
        device = Device(**validated_data)
        raw = device.rotate_api_key()
        device.save()
        device._raw_api_key = raw
        return device

    def to_representation(self, instance):
        data = super().to_representation(instance)
        raw = getattr(instance, '_raw_api_key', None)
        if raw:
            data['api_key'] = raw
        return data
