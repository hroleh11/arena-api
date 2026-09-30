from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class ProfileTestCase(APITestCase):

    def setUp(self) -> None:
        self.tyler = User.objects.create(username='tyler', email='tyler@test.com')
        self.nic = User.objects.create(username='nic', email='nic@test.com')

        self.refresh = RefreshToken.for_user(self.tyler)

    def test_retrieve_myprofile(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh.access_token}')
        response = self.client.get(reverse('myprofile-details_v2'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'tyler')

    def test_retrieve_profile(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh.access_token}')
        response = self.client.get(reverse('profile-details_v2', kwargs={'global_id': self.nic.profile.global_id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'nic')

    def test_update_myprofile(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh.access_token}')
        response = self.client.patch(reverse('myprofile-details_v2'), data={'bio': 'Red monkey'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bio'], 'Red monkey')

    # def test_delete_myprofile(self):
    #     self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh.access_token}')
    #
    # def test_categories_subscription(self):
    #     self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh.access_token}')
    #
    # def test_publishers_subscription(self):
    #     self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh.access_token}')
