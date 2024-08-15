"""
Tests for the tags
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from core.models import Tag, Recipe
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')

def detail_url(tag_id):
    return reverse('recipe:tag-detail', args=[tag_id])

def create_user(email='user@example.com', password='testpass@123'):
    return get_user_model().objects.create_user(email=email, password=password)

class PublicTagsApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrive_tags(self):

        Tag.objects.create(user=self.user, name="sweets")
        Tag.objects.create(user=self.user, name="spicy")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-id')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrive_tags_of_user_only(self):
        """Make sure tags we retrive are only of user who is retriving"""
        user2 = create_user(email="user2@example.com")
        tag = Tag.objects.create(user=user2, name="fruites")
        tag1 = Tag.objects.create(user=self.user, name="drinks")
        tag2 = Tag.objects.create(user=self.user, name="non-veg")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.filter(user=self.user).order_by('-id')
        tags_of_user2 = Tag.objects.filter(user=user2)

        serializer = TagSerializer(tags, many=True)
        serializer2 = TagSerializer(tags_of_user2, many=True)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.data, serializer.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_partial_update_tag(self):
        tag = Tag.objects.create(user=self.user, name="sweets")
        
        payload = {'name':'dessert'}
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_self_user_tag_only(self):
        user2 = create_user(email='user2@example.com')
        tag1 = Tag.objects.create(user=self.user, name="sweets")
        tag2 = Tag.objects.create(user=user2, name="sweets")

        url1 = detail_url(tag1.id)
        url2 = detail_url(tag2.id)
        res1 = self.client.delete(url1)
        res2 = self.client.delete(url2)

        self.assertEqual(res1.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(res2.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn(tag2, Tag.objects.filter(user=user2))
        self.assertNotIn(tag1, Tag.objects.filter(user=self.user))

    def test_update_tag_name_to_existing_name(self):
        """Test updating a tag's name to one that already exists."""
        # Create tags and a recipe manually
        tag1 = Tag.objects.create(user=self.user, name='Dinner')
        tag2 = Tag.objects.create(user=self.user, name='Lunch')
        recipe = Recipe.objects.create(
            user=self.user,
            title="Sample Recipe",
            time_minutes=10,
            price=Decimal("5.00"),
        )
        recipe.tags.add(tag1)

        # Perform the update
        payload = {'name': 'Lunch'}
        url = detail_url(tag1.id)
        res = self.client.patch(url, payload)

        # Assertions
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(Tag.objects.filter(name='Dinner').count(), 0)
        self.assertEqual(Tag.objects.filter(name='Lunch').count(), 1)
        self.assertIn(tag2, recipe.tags.all())