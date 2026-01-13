from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginView,
    MeView,
    TwoFactorDisableView,
    TwoFactorEnableView,
    TwoFactorSetupView,
    TwoFactorVerifyView,
)

urlpatterns = [
    path('auth/login', LoginView.as_view()),
    path('auth/2fa/verify', TwoFactorVerifyView.as_view()),
    path('auth/2fa/setup', TwoFactorSetupView.as_view()),
    path('auth/2fa/enable', TwoFactorEnableView.as_view()),
    path('auth/2fa/disable', TwoFactorDisableView.as_view()),
    path('auth/refresh', TokenRefreshView.as_view()),
    path('auth/me', MeView.as_view()),
]
