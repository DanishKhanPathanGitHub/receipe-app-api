from django.contrib.auth import get_user_model, authenticate

from rest_framework import serializers

from django.utils.translation import gettext as _

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model=get_user_model()
        fields = ['email', 'password', 'name']
        extra_kwargs = {
            'password': {
                'write_only':True,
                'min_length':6,
                'trim_whitespace': False,
            }
        }

    def create(self, validated_data):
        return get_user_model().objects.create_user(**validated_data)
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()
        return user

class ActivateUserSerializer(serializers.Serializer):
    token=serializers.CharField(write_only=True, required=True)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
        
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        style={"input_type":"password"},
        trim_whitespace=False,
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        print(f"AuthTokenSerializer.validate: email={email} password={password}")
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password,
        )
        print(f"AuthTokenSerializer.validate: email={email} password={password} user={user}")
        if not user:
            print(f"User not authenticated: {user}")
            msg = _('Unable to authenticate with provided credentials')
            raise serializers.ValidationError(msg, code='authenticate')
        else:
            attrs['user'] = user
            return attrs

class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    token = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')

        if password != confirm_password:
            raise serializers.ValidationError("Passwords don't match")
        if not password:
            raise serializers.ValidationError("Password cannot be empty")
        return attrs
    