from rest_framework import serializers

from .models import Device


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['id', 'name', 'status', 'last_seen_at', 'created_at']
        read_only_fields = ['id', 'last_seen_at', 'created_at']


class DeviceCreateSerializer(serializers.ModelSerializer):
    api_key = serializers.CharField(read_only=True)

    class Meta:
        model = Device
        fields = ['id', 'name', 'status', 'api_key', 'created_at']
        read_only_fields = ['id', 'api_key', 'created_at']

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
