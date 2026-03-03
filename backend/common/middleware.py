import json
import re
import time

from django.db import connection

from .observability import record_api_event


class ApiTrafficMiddleware:
    API_PREFIX = '/api/'
    OBSERVABILITY_PREFIX = '/api/v1/observability'
    MAX_CAPTURE_SIZE = 5000
    MAX_QUERY_SAMPLE = 25

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith(self.API_PREFIX):
            return self.get_response(request)

        start = time.perf_counter()
        skip_payload_capture = request.path.startswith(self.OBSERVABILITY_PREFIX)
        request_payload = None if skip_payload_capture else self._extract_request_payload(request)
        query_count_start = self._query_count()

        try:
            response = self.get_response(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            record_api_event(
                method=request.method,
                path=request.path,
                query_params=request.GET.dict(),
                status_code=500,
                duration_ms=duration_ms,
                request_payload=request_payload,
                response_payload={'error': exc.__class__.__name__},
                db_query_count=self._query_delta(query_count_start),
                db_activity=self._query_activity(query_count_start),
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        response_payload = (
            {'captured': False, 'reason': 'observability_endpoint'}
            if skip_payload_capture
            else self._extract_response_payload(response)
        )
        record_api_event(
            method=request.method,
            path=request.path,
            query_params=request.GET.dict(),
            status_code=response.status_code,
            duration_ms=duration_ms,
            request_payload=request_payload,
            response_payload=response_payload,
            db_query_count=self._query_delta(query_count_start),
            db_activity=self._query_activity(query_count_start),
        )
        return response

    def _query_count(self):
        if not hasattr(connection, 'queries'):
            return None
        return len(connection.queries)

    def _query_delta(self, start_count):
        if start_count is None or not hasattr(connection, 'queries'):
            return None
        return max(len(connection.queries) - start_count, 0)

    def _query_activity(self, start_count):
        if start_count is None or not hasattr(connection, 'queries'):
            return None

        queries = list(connection.queries[start_count:])
        operations = {}
        tables = {}
        recent = []

        for index, query in enumerate(queries):
            sql = query.get('sql', '')
            operation, table = self._parse_sql_metadata(sql)
            operations[operation] = operations.get(operation, 0) + 1
            if table:
                tables[table] = tables.get(table, 0) + 1

            if index < self.MAX_QUERY_SAMPLE:
                recent.append(
                    {
                        'operation': operation,
                        'table': table,
                        'duration_ms': self._to_ms(query.get('time')),
                    }
                )

        return {
            'count': len(queries),
            'operations': operations,
            'tables': tables,
            'recent': recent,
        }

    def _parse_sql_metadata(self, sql):
        snippet = (sql or '').strip()
        if not snippet:
            return 'unknown', None

        upper = snippet.upper()
        op = upper.split(' ', 1)[0]
        op = op if op in {'SELECT', 'INSERT', 'UPDATE', 'DELETE'} else 'OTHER'

        table = None
        table_patterns = (
            re.compile(r'\bFROM\s+[`"]?([\w.]+)[`"]?', re.IGNORECASE),
            re.compile(r'\bINTO\s+[`"]?([\w.]+)[`"]?', re.IGNORECASE),
            re.compile(r'\bUPDATE\s+[`"]?([\w.]+)[`"]?', re.IGNORECASE),
        )
        for pattern in table_patterns:
            match = pattern.search(snippet)
            if match:
                table = match.group(1)
                break

        return op.lower(), table

    def _to_ms(self, value):
        try:
            return round(float(value) * 1000, 3)
        except (TypeError, ValueError):
            return None

    def _extract_request_payload(self, request):
        if request.method not in {'POST', 'PUT', 'PATCH', 'DELETE'}:
            return None

        content_type = (request.content_type or '').lower()
        if 'application/json' not in content_type:
            return {'content_type': content_type, 'captured': False}

        raw = request.body or b''
        if len(raw) > self.MAX_CAPTURE_SIZE:
            raw = raw[: self.MAX_CAPTURE_SIZE]

        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            return {'captured': False, 'reason': 'decode_error'}

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    def _extract_response_payload(self, response):
        content_type = (response.get('Content-Type') or '').lower()
        if 'application/json' not in content_type:
            return {'content_type': content_type, 'captured': False}

        try:
            raw = response.content or b''
        except Exception:
            return {'captured': False, 'reason': 'streaming_response'}

        if len(raw) > self.MAX_CAPTURE_SIZE:
            raw = raw[: self.MAX_CAPTURE_SIZE]

        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            return {'captured': False, 'reason': 'decode_error'}

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
