import os

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def root_view(request):
    return JsonResponse(
        {
            'service': 'Agrolink API',
            'status': 'ok',
            'frontend_url': os.getenv('FRONTEND_URL', 'http://localhost:8080'),
            'endpoints': {
                'admin': '/admin/',
                'api': '/api/v1/',
                'api_catalog': '/api/v1/api-catalog',
                'observability': '/api/v1/observability',
            },
        }
    )


urlpatterns = [
    path('', root_view),
    path('admin/', admin.site.urls),
    path('api/v1/', include('common.urls')),
    path('api/v1/', include('users.urls')),
    path('api/v1/', include('devices.urls')),
    path('api/v1/', include('telemetry.urls')),
]
