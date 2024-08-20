from django.core.mail import EmailMessage
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponse
from django.shortcuts import reverse
from django.conf import settings
from rest_framework import generics, authentication, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from .serializers import *
import secrets


class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer
    def perform_create(self, serializer):
        user = serializer.save(is_active=False)  # Create inactive user
        user.set_email_token()
        user.save()
        print(user.email_token)
        subject = 'Activate your account'
        message = f'Hi {user.name}, activate your account \n token: {user.email_token}'
        
        email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        email.send()

class ActivateUserView(APIView):
    serializer_class = ActivateUserSerializer
    def post(self, request):
        serializer = ActivateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        print(token)
        user = get_user_model().objects.filter(email_token=token).first()
        if user and user.is_email_token_valid(token):
            user.is_active = True
            user.clear_email_token()
            user.save()
            return HttpResponse('Your account has been activated', status=200)
        else:
            return HttpResponse('Activation link is invalid', status=400)

class ForgotPasswordView(APIView):
    serializer_class = ForgotPasswordSerializer

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = get_user_model().objects.filter(email=email).first()
        
        if user:
            user.set_email_token()
            print(user.email_token)
            user.save()
            # Send email
            subject = 'Password Reset'
            message = f'Use the token below to reset password: \n Token: {user.email_token}'
            email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
            email.send()
        
        return Response({"message": "we have sent token to your email, \n use it while reseting password."}, status=status.HTTP_200_OK)

class ResetPasswordView(APIView):
    serializer_class = ResetPasswordSerializer

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        print(token)
        user = get_user_model().objects.filter(email_token=token).first()

        if user and user.is_email_token_valid(token):
            user.set_password(serializer.validated_data['password'])
            user.clear_email_token()
            user.save()
            return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)



class AuthTokenView(ObtainAuthToken):
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
