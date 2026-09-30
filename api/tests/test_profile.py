from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from api.errors import EDIT_PROFILE

User = get_user_model()


class ProfileTestCase(APITestCase):

    def setUp(self) -> None:
        self.user = User.objects.create(username='test', email='test@gmail.com', password='secret')
        self.profile = self.user.profile

        self.refresh = RefreshToken.for_user(self.user)

    def test_my_profile(self):
        response = self.client.get(reverse('profile-details'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh.access_token}')
        response = self.client.get(reverse('profile-details'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_profile(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh.access_token}')

        response = self.client.patch(reverse('profile-details'), data={'name': ''})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': [ErrorDetail(EDIT_PROFILE['PROFILE'], code='invalid')]})

        response = self.client.patch(reverse('profile-details'), data={'username': ''})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': [ErrorDetail(EDIT_PROFILE['PROFILE'], code='invalid')]})

        response = self.client.patch(reverse('profile-details'), data={'website': 'wrong url'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': [ErrorDetail(EDIT_PROFILE['PROFILE'], code='invalid')]})

        response = self.client.patch(reverse('profile-details'), data={'bio': 'more than 150 characters'*10})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': [ErrorDetail(EDIT_PROFILE['PROFILE'], code='invalid')]})
