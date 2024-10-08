from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer
from decimal import Decimal
from core.models import Recipe, Tag, Ingredient

import tempfile
import os
from PIL import Image

from rest_framework import status
from rest_framework.test import APIClient

RECIPES_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])

def image_upload_url(recipe_id):
    return reverse('recipe:recipe-upload-image', args=[recipe_id])

def create_recipe(user, **params):
    defaults = {
        "title":"sample recipe title",
        "time_minutes":5,
        "price":Decimal("10.50"),
        "description":"sample recipe description",
        "link":"https://example.com//recipe.pdf",
    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)

class PublicRecipeAPITests(TestCase):
    """Test unauthetnticated API test"""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateRecipeAPITests(TestCase):
    """Test unauthetnticated API test"""
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@exampl.com",
            "testpass@123",
        )
        self.client.force_authenticate(self.user)

    def test_retrive_recipes(self):
        create_recipe(user=self.user)
        create_recipe(user=self.user)
        
        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrive_recipes_of_user_for_user(self):
        
        other_user = get_user_model().objects.create_user(
            "test123@example.com",
            "testpass@123",
        )
        create_recipe(user=self.user)
        create_recipe(user=other_user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):

        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)
        print(serializer.data)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_recipe(self):
        payload = {
            "title":"sample recipe title",
            "time_minutes":5,
            "price":Decimal("10.50"),
            "description":"sample recipe description",
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        self.assertEqual(recipe.user, self.user)

    def test_recipe_partial_update(self):
        """testing patch working correctly"""
        recipe = create_recipe(user=self.user)
        #This will have title set to default "title":"sample recipe title"
        #other defaults are "time_minutes":5, "price":Decimal("10.50"),
        payload = {"title":"New recipe title"}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.price, Decimal("10.50"))
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.user, self.user)

    def test_recipe_full_update(self):
        """testing PUT method works correctly"""
        recipe = create_recipe(user=self.user)
        payload = {
            "title":"New recipe title",
            "time_minutes":6,
            "price":Decimal("12.20"),
            "description":"sample recipe description updated",
            "link":"https://example.com//updated-recipe.pdf",
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_self_recipe_only(self):
        """Testing users only allowed to update the recipes owned by them"""
        other_user = get_user_model().objects.create_user(
            "test123@example.com",
            "testpass@123",
        )
        recipe = create_recipe(user=other_user)
        url = detail_url(recipe.id)
        payload = {"title":"New recipe title", "user":self.user}
        self.client.patch(url, payload)
    
        self.assertTrue(recipe)    
        self.assertEqual(recipe.user, other_user)

    def test_delete_recipe(self):
        recipe = create_recipe(user=self.user)
        recipe2 = create_recipe(user=self.user)
        recipes = Recipe.objects.all()
        url = detail_url(recipe2.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        self.assertIn(recipe, recipes)
        self.assertNotIn(recipe2, recipes)

    def test_delete_self_recipe_only(self):
        other_user = get_user_model().objects.create_user(
            "test123@example.com",
            "testpass@123",
        )
        recipe = create_recipe(user=other_user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())
        self.assertEqual(recipe.user, other_user)

    def test_create_recipe_with_new_tag(self):
        payload = {
            "title":"bluebarry cake",
            "time_minutes":25,
            "price":Decimal("20.50"),
            "tags": [
                {"name":"sweet"},
                {"name":"dessert"}
            ],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        tag_indian = Tag.objects.create(user=self.user, name="Indian")
        payload = {
            "title":"paratha",
            "time_minutes":25,
            "price":Decimal("12.00"),
            "tags": [{"name":"Indian"}, {"name":"breakfast"}],
        }
        res = self.client.post(RECIPES_URL,  payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)   

    def test_create_tag_on_update(self):
        recipe = create_recipe(user=self.user)
        payload = {'tags':[{'name':'Lunch'}]}
        
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Lunch')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        recipe = create_recipe(user=self.user)
        tag_indian = Tag.objects.create(user=self.user, name="Indian")
        recipe.tags.add(tag_indian)
        
        tag_italian = Tag.objects.create(user=self.user, name="Italian")
        payload = {'tags':[{'name':'Italian'}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 1)
        self.assertIn(tag_italian, recipe.tags.all())

    def test_clear_recipe_tags(self):
        tag = Tag.objects.create(user=self.user, name="sweet")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags':[]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
        

    def test_create_recipe_with_new_and_existingingredients(self):
        """
        Checks recipe creation with new ingredient and existing ingredient
        both in one test
        """
        payload = {
            "title":"sample recipe title",
            "time_minutes":5,
            "price":Decimal("10.50"),
            "ingredients":[
                {"name":"water"},
                {"name":"soda"},
            ],
        }
        existing_ing = Ingredient.objects.create(name="water", user=self.user)
        res = self.client.post(RECIPES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        
        recipe = recipes[0]
        self.assertIn(existing_ing, recipe.ingredients.all())
        self.assertEqual(recipe.ingredients.count(), 2)
        
        for ing in payload['ingredients']:
            self.assertTrue(
                recipe.ingredients.filter(
                    name=ing['name'], user=self.user
                ).exists()
            )
    
    def test_create_or_assign_ingredients_on_recipe_update(self):
        ing = Ingredient.objects.create(name="soda", user=self.user)
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ing)

        payload = {
            "ingredients":[
                {"name":"soda"},
                {"name":"water"},
            ]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(Ingredient.objects.all().count(), 2)
        self.assertIn(ing, recipe.ingredients.all())

    def test_clear_recipe_ingredientss(self):
        ing = Ingredient.objects.create(user=self.user, name="salt")
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ing)

        payload = {'ingredients':[]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)

class ImageUploadTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'password123',
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10,10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image':image_file}
            res = self.client.post(url, payload, format="multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        url = image_upload_url(self.recipe.id)

        # Create and write to a temporary file, then use it for the request
        with tempfile.NamedTemporaryFile(suffix='.txt', mode='w+b', delete=False) as temp_file:
            temp_file.write(b'This is not an image')
            temp_file.seek(0)
            
            # Prepare the payload with the temporary file
            payload = {'image': temp_file}
            res = self.client.post(url, payload, format="multipart")

        # Check that the response status code is 400 Bad Request
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('image', res.data)
        self.assertTrue('valid image' in res.data['image'][0])

        # Clean up temporary file
        os.remove(temp_file.name)