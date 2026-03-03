from django.urls import path

from .views import ApiCatalogView, ObservabilityClearView, ObservabilityDashboardView

urlpatterns = [
    path('api-catalog', ApiCatalogView.as_view()),
    path('observability', ObservabilityDashboardView.as_view()),
    path('observability/clear', ObservabilityClearView.as_view()),
]
