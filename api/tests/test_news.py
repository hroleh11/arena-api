from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from api.models import Categories, ColumnNews

User = get_user_model()

data = {
    'user': {'username': 'user', 'email': 'user@vylo.com'},
    'category': {'name': 'Sport', 'is_active': True},
    'news': {'title': 'Title', 'link': None}
}


class NewsAPITestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create(**data['user'])
        self.profile = self.user.profile
        self.category = Categories.objects.create(**data['category'])
        self.news = ColumnNews.objects.create(category=self.category, publisher=self.profile, **data['news'])

        self.refresh_user = RefreshToken.for_user(self.user)

    def test_user_news(self):
        response = self.client.get(reverse('news-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh_user.access_token}')
        response = self.client.get(reverse('news-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_news_update(self):
        url = reverse('news-details', args=(self.news.global_id,))
        data = {'title': 'Title 2', 'category_global_id': str(self.category.global_id), 'link': 'https://google.com'}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh_user.access_token}')
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.news.refresh_from_db()
        self.assertEqual(self.news.title, 'Title 2')

    def test_news_report(self):
        data = {
            'status': 1,
            'news_global_id': str(self.news.global_id),
            'link': 'https://google.com'
        }
        response = self.client.post(reverse('news-report'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh_user.access_token}')
        response = self.client.post(reverse('news-report'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_news_delete(self):
        url = reverse('news-details', args=(self.news.global_id,))
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh_user.access_token}')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.news.refresh_from_db()
        self.assertEqual(self.news.status, ColumnNews.Statuses.DELETED)
