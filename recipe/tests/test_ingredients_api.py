from django.contrib.auth import get_user_model
from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer
from django.test import TestCase

from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

INGREDIENT_URL = reverse("recipe:ingredient-list")

def detail_url(ing_id):
    return reverse('recipe:ingredient-detail', args=[ing_id])

def create_user(email='user@example.com', password='testpass@123'):
    return get_user_model().objects.create_user(email=email, password=password)

class PublicIngredientsApiTest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateIngredientsApiTests(TestCase):

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrive_ingredients_and_of_user_only(self):
        user2 = create_user(email="user2@example.com")

        ing1 = Ingredient.objects.create(name="salt", user=self.user)
        ing2 = Ingredient.objects.create(name="wheat", user=self.user)
        ing3 = Ingredient.objects.create(name="spices", user=user2)

        res = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.filter(user=self.user).order_by("-id")
        ingredients2 = Ingredient.objects.filter(user=user2).order_by("-id")
        serializer = IngredientSerializer(ingredients, many=True)
        serializer2 = IngredientSerializer(ingredients2, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_update_ingredient(self):
        ingredient = Ingredient.objects.create(name="ingredient", user=self.user)
        payload = {
            "name":"salt"
        }
        res = self.client.patch(detail_url(ingredient.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload["name"])

    def test_delete_ingredient_and_of_user_only(self):
        user2 = create_user(email="user2@example.com")
        ing1 = Ingredient.objects.create(name="salt", user=self.user)
        Ingredient.objects.create(name="black papper", user=self.user)
        Ingredient.objects.create(name="salt", user=user2)

        url = detail_url(ing1.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Ingredient.objects.all().count(), 2)

