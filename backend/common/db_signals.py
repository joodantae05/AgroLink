from django.apps import apps
from django.db.models.signals import post_delete, post_save

from .observability import record_db_event


_REGISTERED = False

_OBSERVED_MODELS = [
    'devices.Device',
    'telemetry.Reading',
    'telemetry.Threshold',
    'telemetry.Alert',
    'users.Profile',
    'auth.User',
]

_KEY_FIELDS = {
    'id',
    'name',
    'status',
    'email',
    'username',
    'totp_enabled',
    'sensor_type',
    'value',
    'unit',
    'measured_at',
    'triggered_at',
    'resolved_at',
    'created_at',
    'last_seen_at',
    'device_id',
    'owner_id',
    'user_id',
}


def _serialize_instance(instance):
    payload = {}
    for field in instance._meta.fields:
        name = field.name
        if name in _KEY_FIELDS or name.endswith('_id'):
            value = getattr(instance, name, None)
            if hasattr(value, 'isoformat'):
                value = value.isoformat()
            payload[name] = value
    return payload


def _on_post_save(sender, instance, created, **kwargs):
    record_db_event(
        action='insert' if created else 'update',
        model=sender._meta.label,
        pk=instance.pk,
        payload=_serialize_instance(instance),
    )


def _on_post_delete(sender, instance, **kwargs):
    record_db_event(
        action='delete',
        model=sender._meta.label,
        pk=instance.pk,
        payload=_serialize_instance(instance),
    )


def register_db_signals():
    global _REGISTERED
    if _REGISTERED:
        return

    for model_label in _OBSERVED_MODELS:
        try:
            model = apps.get_model(model_label)
        except LookupError:
            continue

        post_save.connect(
            _on_post_save,
            sender=model,
            dispatch_uid=f'observability-save-{model_label}',
            weak=False,
        )
        post_delete.connect(
            _on_post_delete,
            sender=model,
            dispatch_uid=f'observability-delete-{model_label}',
            weak=False,
        )

    _REGISTERED = True
