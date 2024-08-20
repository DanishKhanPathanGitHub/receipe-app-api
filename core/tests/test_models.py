"""
Tests for models
"""
from django.test import TestCase
from unittest.mock import patch
import os

from django.contrib.auth import get_user_model
from decimal import Decimal
from core import models

class ModelTests(TestCase):
    """Testing the models"""
    
    def test_create_user_with_email_succeesfull(self):
        email = "test@example.com"
        password = "testpass@123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )
        self.assertEqual(user.email, email)
        print(f'user with email: {user.email} created')
        self.assertTrue(user.check_password(password))
        print(f'user password: {user.password} set')
    
    def test_new_user_email_normalized(self):
        sample_emails =[
            ['test1@ExaMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'testpass123')
            self.assertEqual(user.email, expected)

    def test_new_user_wo_email_raises_error(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')
        
    def test_create_superuser(self):
        user = get_user_model().objects.create_superuser('test1@gmail.com', 'test123')
        self.assertEqual(user.email, 'test1@gmail.com')
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)


    def test_create_recipe(self):

        user = get_user_model().objects.create_user(
            "test@example.com",
            "testpass@123",
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title="sample recipe title",
            time_minutes=5,
            price=Decimal("10.50"),
            description="sample recipe description"
        )
        self.assertEqual(str(recipe), "sample recipe title")

    def test_create_tag(self):
        user = get_user_model().objects.create_user(
            "test@example.com",
            "testpass@123",
        )
        tag = models.Tag.objects.create(user=user, name="Tag1")

        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        user = get_user_model().objects.create_user(
            "test@example.com",
            "testpass@123",
        )
        ingredient = models.Ingredient.objects.create(user=user, name="Ingredient1")

        self.assertEqual(str(ingredient), ingredient.name)
        
    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid

        file_path = models.recipe_image_file_path(None, 'example.jpg')
        print(file_path)
        self.assertEqual(file_path, os.path.join('uploads', 'recipe', f'{uuid}.jpg'))
        