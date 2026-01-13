import secrets
import uuid

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import models


class Device(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='devices')
    name = models.CharField(max_length=120)
    api_key_hash = models.CharField(max_length=128)
    api_key_prefix = models.CharField(max_length=8)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='active')
    last_seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def rotate_api_key(self):
        raw = secrets.token_urlsafe(32)
        self.api_key_hash = make_password(raw)
        self.api_key_prefix = raw[:8]
        return raw

    def __str__(self):
        return f'{self.name} ({self.id})'
