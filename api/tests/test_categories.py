from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.serializers.categories import CategoriesSerializer
from api.models import Categories

User = get_user_model()


class CategoriesTestCase(APITestCase):

    def setUp(self) -> None:
        self.category = Categories.objects.create(name='sport', is_active=True)
        self.category.subcategories.set([Categories.objects.create(name="football", is_active=False)])

    def test_categories_list(self):
        data = CategoriesSerializer(self.category).data
        response = self.client.get(reverse('categories-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0], data)
