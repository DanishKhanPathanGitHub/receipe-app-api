"""
Database models
"""
import os
import uuid
import secrets
from datetime import timedelta
from app import settings
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

def recipe_image_file_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'
    return os.path.join('uploads', 'recipe', filename)

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **kwargs):
        if not email:
            raise ValueError("users must have email")
        user = self.model(email=self.normalize_email(email), **kwargs)
        user.set_password(password)
        user.save(using=self._db)     
        
        return user   
    
    def create_superuser(self, email, password, **kwargs):
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_active = True
        user.is_superuser = True
        user.save(using=self._db)

        return user

class User(AbstractBaseUser, PermissionsMixin):

    email = models.EmailField(max_length=254, unique=True)
    name = models.CharField(max_length=250)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    email_token = models.CharField(max_length=64, blank=True, null=True)
    token_created_at = models.DateTimeField(blank=True, null=True)
    token_expiration = models.DateTimeField(blank=True, null=True)

    objects = UserManager()
    USERNAME_FIELD = 'email'

    def set_email_token(self):
        """Generates a new reset token and sets its expiration time."""
        self.email_token = secrets.token_hex(4)
        self.token_expiration = timezone.now() + timedelta(minutes=4)
        self.save()

    def clear_email_token(self):
        """Clears the reset token and its expiration time."""
        self.email_token = None
        self.token_expiration = None
        self.save()

    def is_email_token_valid(self, token):
        """Checks if the provided token is valid and not expired."""
        return self.email_token == token and self.token_expiration > timezone.now()

class Recipe(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    time_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    link = models.CharField(max_length=255, blank=True)
    tags = models.ManyToManyField('Tag')
    ingredients = models.ManyToManyField("Ingredient")
    image = models.ImageField(null=True, upload_to=recipe_image_file_path)

    def __str__(self) -> str:
        return self.title
        
    
class Tag(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return str(self.name)
    
class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return str(self.name)