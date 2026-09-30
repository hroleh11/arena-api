from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APITestCase

from api.errors import FORGOT_PASSWORD
from api.models import ResetCode

User = get_user_model()


class SingUpTestCase(APITestCase):

    def setUp(self) -> None:
        self.user = User.objects.create(username='tyler', email='tyler@test.com')

    def test_check_email_valid(self):
        response = self.client.post(reverse('draft-user'), {'email': 'tyler@test.com'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('is_valid', None), False)

        response = self.client.post(reverse('draft-user'), {'email': 'nic@test.com'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('is_valid', None), True)


class ForgotPasswordTestCase(APITestCase):

    def setUp(self) -> None:
        self.user = User.objects.create(username='tyler', email='tyler@test.com')
        self.user.set_password('super_strong')
        self.user.save()

    def test_reset_password(self):
        response = self.client.post(reverse('user-reset-password'), data={'email': 'tyler@test.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {
            'code': ResetCode.objects.get(user=self.user).code,
            'token': response.data['token'],
            'new_password': 'fdsfs',
            're_new_password': 'fsdfas'
        }

        response = self.client.post(reverse('user-reset-password-confirm'), data=data)
        error_detail = ErrorDetail(FORGOT_PASSWORD['CONFIRM-PASSWORD_MATCH'], code='invalid')
        self.assertEqual(response.data, {'new_password': [error_detail]})
