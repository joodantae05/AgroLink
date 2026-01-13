import pyotp

from django.contrib.auth import authenticate, get_user_model
from django.core import signing
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Profile
from .serializers import UserSerializer
from .services import issue_tokens


User = get_user_model()
TEMP_TOKEN_SALT = 'agrolink-2fa'
TEMP_TOKEN_TTL = 300


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        identifier = request.data.get('username') or request.data.get('email')
        password = request.data.get('password')
        if not identifier or not password:
            return Response({'detail': 'Missing credentials'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(Q(username=identifier) | Q(email=identifier)).first()
        if not user:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        user = authenticate(request, username=user.username, password=password)
        if not user:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        profile = Profile.objects.get(user=user)
        if profile.totp_enabled:
            temp_token = signing.dumps({'user_id': user.id}, salt=TEMP_TOKEN_SALT)
            return Response({'requires_2fa': True, 'temp_token': temp_token})

        tokens = issue_tokens(user)
        return Response({'requires_2fa': False, **tokens})


class TwoFactorVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        temp_token = request.data.get('temp_token')
        code = request.data.get('code')
        if not temp_token or not code:
            return Response({'detail': 'Missing data'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = signing.loads(temp_token, salt=TEMP_TOKEN_SALT, max_age=TEMP_TOKEN_TTL)
        except signing.BadSignature:
            return Response({'detail': 'Invalid or expired token'}, status=status.HTTP_401_UNAUTHORIZED)

        user = User.objects.filter(id=data.get('user_id')).first()
        if not user:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        profile = Profile.objects.get(user=user)
        totp = profile.ensure_totp_secret()
        if not pyotp.TOTP(totp).verify(code, valid_window=1):
            return Response({'detail': 'Invalid code'}, status=status.HTTP_401_UNAUTHORIZED)

        tokens = issue_tokens(user)
        return Response(tokens)


class TwoFactorSetupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = Profile.objects.get(user=request.user)
        secret = profile.ensure_totp_secret()
        return Response({'secret': secret, 'otpauth_uri': profile.provisioning_uri()})


class TwoFactorEnableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get('code')
        if not code:
            return Response({'detail': 'Missing code'}, status=status.HTTP_400_BAD_REQUEST)

        profile = Profile.objects.get(user=request.user)
        secret = profile.ensure_totp_secret()
        if not pyotp.TOTP(secret).verify(code, valid_window=1):
            return Response({'detail': 'Invalid code'}, status=status.HTTP_401_UNAUTHORIZED)

        profile.totp_enabled = True
        profile.save(update_fields=['totp_enabled'])
        return Response({'enabled': True})


class TwoFactorDisableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get('code')
        if not code:
            return Response({'detail': 'Missing code'}, status=status.HTTP_400_BAD_REQUEST)

        profile = Profile.objects.get(user=request.user)
        if not profile.totp_secret:
            return Response({'detail': '2FA not configured'}, status=status.HTTP_400_BAD_REQUEST)

        if not pyotp.TOTP(profile.totp_secret).verify(code, valid_window=1):
            return Response({'detail': 'Invalid code'}, status=status.HTTP_401_UNAUTHORIZED)

        profile.totp_enabled = False
        profile.save(update_fields=['totp_enabled'])
        return Response({'enabled': False})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
