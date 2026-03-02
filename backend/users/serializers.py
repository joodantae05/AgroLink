from django.contrib.auth import get_user_model
from rest_framework import serializers


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=False, trim_whitespace=True, max_length=150)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(trim_whitespace=False, max_length=128)

    def validate(self, attrs):
        if not attrs.get('username') and not attrs.get('email'):
            raise serializers.ValidationError('username or email is required.')
        return attrs


class TempTokenCodeSerializer(serializers.Serializer):
    temp_token = serializers.CharField(max_length=2048)
    code = serializers.RegexField(regex=r'^\d{6}$')


class TotpCodeSerializer(serializers.Serializer):
    code = serializers.RegexField(regex=r'^\d{6}$')
