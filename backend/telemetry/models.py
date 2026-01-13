import uuid

from django.db import models

from common.constants import SENSOR_TYPES
from devices.models import Device


class Reading(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='readings')
    sensor_type = models.CharField(max_length=32, choices=SENSOR_TYPES)
    value = models.FloatField()
    unit = models.CharField(max_length=16)
    measured_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


class Threshold(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='thresholds')
    sensor_type = models.CharField(max_length=32, choices=SENSOR_TYPES)
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Alert(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='alerts')
    sensor_type = models.CharField(max_length=32, choices=SENSOR_TYPES)
    value = models.FloatField()
    triggered_at = models.DateTimeField()
    resolved_at = models.DateTimeField(null=True, blank=True)
