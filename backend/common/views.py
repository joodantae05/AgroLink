from django.conf import settings
from django.urls import URLPattern, URLResolver, get_resolver
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .observability import build_dashboard, clear_events


def _collect_routes(urlpatterns, prefix=''):
    routes = []
    for entry in urlpatterns:
        if isinstance(entry, URLPattern):
            routes.append(prefix + str(entry.pattern))
        elif isinstance(entry, URLResolver):
            routes.extend(_collect_routes(entry.url_patterns, prefix + str(entry.pattern)))
    return routes


class DebugAwareAPIView(APIView):
    def get_permissions(self):
        classes = [AllowAny] if settings.DEBUG else [IsAuthenticated]
        return [permission() for permission in classes]


class ApiCatalogView(DebugAwareAPIView):
    def get(self, request):
        resolver = get_resolver()
        routes = sorted(set(_collect_routes(resolver.url_patterns)))
        return Response(
            {
                'count': len(routes),
                'routes': routes,
                'note': 'Visualisation des routes backend disponibles.',
            }
        )


class ObservabilityDashboardView(DebugAwareAPIView):
    def get(self, request):
        try:
            limit = int(request.query_params.get('limit', '100'))
        except ValueError:
            limit = 100

        limit = max(10, min(limit, 500))
        dashboard = build_dashboard(limit=limit)
        dashboard['note'] = (
            "api_traffic = ce qui rentre/sort via l'API, "
            "db_events = insert/update/delete observes sur la base."
        )
        return Response(dashboard)


class ObservabilityClearView(DebugAwareAPIView):
    def post(self, request):
        clear_events()
        return Response({'cleared': True})
