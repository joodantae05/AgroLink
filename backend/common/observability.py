import os
import threading
from collections import deque
from datetime import datetime
from typing import Any


def _to_int(value: str, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


MAX_EVENTS = max(100, _to_int(os.getenv('OBSERVABILITY_MAX_EVENTS', '500'), 500))
_API_EVENTS = deque(maxlen=MAX_EVENTS)
_DB_EVENTS = deque(maxlen=MAX_EVENTS)
_LOCK = threading.Lock()

_SENSITIVE_TOKENS = (
    'password',
    'token',
    'secret',
    'api_key',
    'authorization',
    'cookie',
)


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(token in lowered for token in _SENSITIVE_TOKENS)


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            if _is_sensitive_key(str(key)):
                sanitized[str(key)] = '[REDACTED]'
            else:
                sanitized[str(key)] = _sanitize(item)
        return sanitized

    if isinstance(value, (list, tuple, set)):
        return [_sanitize(item) for item in value]

    if isinstance(value, bytes):
        text = value.decode('utf-8', errors='replace')
        return text if len(text) <= 1000 else f'{text[:1000]}...[truncated]'

    if isinstance(value, datetime):
        return value.isoformat()

    if value is None or isinstance(value, (bool, int, float)):
        return value

    text = str(value)
    return text if len(text) <= 300 else f'{text[:300]}...[truncated]'


def record_api_event(
    *,
    method: str,
    path: str,
    query_params: dict[str, Any] | None,
    status_code: int,
    duration_ms: float,
    request_payload: Any = None,
    response_payload: Any = None,
    db_query_count: int | None = None,
    db_activity: dict[str, Any] | None = None,
):
    event = {
        'at': datetime.utcnow().isoformat() + 'Z',
        'method': method,
        'path': path,
        'query_params': _sanitize(query_params or {}),
        'status_code': status_code,
        'duration_ms': round(duration_ms, 2),
        'db_query_count': db_query_count,
        'db_activity': _sanitize(db_activity),
        'request_payload': _sanitize(request_payload),
        'response_payload': _sanitize(response_payload),
    }
    with _LOCK:
        _API_EVENTS.append(event)


def record_db_event(*, action: str, model: str, pk: str, payload: dict[str, Any] | None = None):
    event = {
        'at': datetime.utcnow().isoformat() + 'Z',
        'action': action,
        'model': model,
        'pk': str(pk),
        'payload': _sanitize(payload or {}),
    }
    with _LOCK:
        _DB_EVENTS.append(event)


def get_api_events(limit: int = 100) -> list[dict[str, Any]]:
    with _LOCK:
        events = list(_API_EVENTS)
    return list(reversed(events[-limit:]))


def get_db_events(limit: int = 100) -> list[dict[str, Any]]:
    with _LOCK:
        events = list(_DB_EVENTS)
    return list(reversed(events[-limit:]))


def clear_events():
    with _LOCK:
        _API_EVENTS.clear()
        _DB_EVENTS.clear()


def build_dashboard(limit: int = 100) -> dict[str, Any]:
    api_events = get_api_events(limit)
    db_events = get_db_events(limit)
    return {
        'max_events': MAX_EVENTS,
        'api_traffic': {
            'count': len(api_events),
            'recent': api_events,
        },
        'db_events': {
            'count': len(db_events),
            'recent': db_events,
        },
    }
