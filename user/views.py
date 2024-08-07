from django.shortcuts import render

# Create your views here.
from .serializers import UserSerializer, AuthTokenSerializer
from rest_framework import generics

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings


class CreateUserView(generics.CreateAPIView):
    serializer_class=UserSerializer

class AuthTokenView(ObtainAuthToken):
    serializer_class=AuthTokenSerializer
    renderer_classes=api_settings.DEFAULT_RENDERER_CLASSES
    