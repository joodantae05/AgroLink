from rest_framework import serializers

from .models import Reading


class ReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reading
        fields = ['id', 'device', 'sensor_type', 'value', 'unit', 'measured_at']
        read_only_fields = ['id']
