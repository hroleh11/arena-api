from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

users_data = {
    'admin': {'email': 'admin@vylo.com', 'username': 'admin', 'is_staff': True, 'is_active': True, 'password': 'admin'},
    'user': {'email': 'user@vylo.com', 'username': 'user', 'password': 'user'},
    'publ': {'email': 'publisher@vylo.com', 'username': 'publisher', 'password': 'publisher'}
}


class UserTestCase(APITestCase):

    def test_publishers(self):
        pass

    def test_newsstand(self):
        pass

    def test_vylo_publishers(self):
        pass

    def test_my_profile(self):
        pass

    def test_profile_following(self):
        pass

    def test_profile_followers(self):
        pass

    def test_retrieve_profile(self):
        pass

    def test_profile_image(self):
        pass

    def test_categories_subscription(self):
        pass

    def test_publishers_subscription(self):
        pass


# class StaffAPITestCase(APITestCase):
#     def setUp(self) -> None:
#         self.admin = User.objects.create(**users_data['admin'])
#         self.refresh_admin = RefreshToken.for_user(self.admin)
#
#     def test_list_staff_users(self):
#         response = self.client.get(reverse('staff-list'))
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh_admin.access_token}')
#         response = self.client.get(reverse('staff-list'))
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#     def test_create_staff_user(self):
#         admin_data = {
#             'email_in_use': {
#                 'email': 'admin@vylo.com', 'name': 'admin_user', 'username': 'admin_user',
#                 'is_superadmin': True, 'is_active': True
#             },
#             'username_in_use': {
#                 'email': 'admin_user@vylo.com', 'name': 'admin', 'username': 'admin',
#                 'is_superadmin': True, 'is_active': True
#             },
#             'trust': {
#                 'email': 'admin_user@vylo.com', 'name': 'admin_user', 'username': 'admin_user',
#                 'is_superadmin': True, 'is_active': True
#             }
#         }
#         data = admin_data['email_in_use']
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh_admin.access_token}')
#         response = self.client.post(reverse('staff-create'), data=data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#
#         data = admin_data['username_in_use']
#         response = self.client.post(reverse('staff-create'), data=data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#
#         data = admin_data['trust']
#         response = self.client.post(reverse('staff-create'), data=data)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#
#         self.client.credentials(HTTP_AUTHORIZATION='')
#         response = self.client.post(reverse('staff-create'), data=data)
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#
#     def test_update_staff_user(self):
#         pk = self.admin.id
#         admin_data = {
#             'update_email': {
#                 'email': 'admin_update@vylo.com', 'name': 'admin', 'username': 'admin',
#                 'is_superadmin': True, 'is_active': True
#             },
#             'update_username': {
#                 'email': 'admin_update@vylo.com', 'name': 'admin_update', 'username': 'admin_update',
#                 'is_superadmin': True, 'is_active': True
#             },
#             'update_not_active': {
#                 'email': 'admin_update@vylo.com', 'name': 'admin_update', 'username': 'admin_update',
#                 'is_superadmin': False, 'is_active': False
#             }
#         }
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh_admin.access_token}')
#
#         data = admin_data['update_email']
#         response = self.client.put(reverse('staff-update', args=(pk,)), data=data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#         data = admin_data['update_username']
#         response = self.client.put(reverse('staff-update', args=(pk,)), data=data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#         data = admin_data['update_not_active']
#         response = self.client.put(reverse('staff-update', args=(pk,)), data=data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#         response = self.client.put(reverse('staff-update', args=(pk,)), data=data)
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#
#         self.client.credentials(HTTP_AUTHORIZATION='')
#         response = self.client.put(reverse('staff-update', args=(pk,)), data=data)
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#
#
# # TODO Upload photo
# class AppUserTestCase(APITestCase):
#     def setUp(self) -> None:
#         self.admin = User.objects.create(**users_data['admin'])
#         self.user = User.objects.create(**users_data['user'])
#
#         self.refresh_admin = RefreshToken.for_user(self.admin)
#
#     def test_list_app_users(self):
#         response = self.client.get(reverse('user-list'))
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh_admin.access_token}')
#         response = self.client.get(reverse('user-list'))
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#     def test_create_app_user(self):
#         user_data = {
#             'email_in_use': {
#                 'email': 'user@vylo.com', 'name': 'app_user', 'username': 'app_user',
#                 'website': 'https://google.com/', 'bio': 'Some description about user',
#                 'phone': '', 'gender': 'other', 'is_active': True, 'is_source': False,
#                 'profile_photo': ''
#             },
#             'username_in_use': {
#                 'email': 'app_user@vylo.com', 'name': 'user', 'username': 'user',
#                 'website': 'https://google.com/', 'bio': 'Some description about user',
#                 'phone': '', 'gender': 'other', 'is_active': True, 'is_source': False,
#                 'profile_photo': ''
#             },
#             'trust': {
#                 'email': 'app_user@vylo.com', 'name': 'app_user', 'username': 'app_user',
#                 'website': 'https://google.com/', 'bio': 'Some description about user',
#                 'phone': '', 'gender': 'other', 'is_active': True, 'is_source': False,
#                 'profile_photo': ''
#             },
#         }
#         data = user_data['email_in_use']
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh_admin.access_token}')
#         response = self.client.post(reverse('user-create'), data=data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#
#         data = user_data['username_in_use']
#         response = self.client.post(reverse('user-create'), data=data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#
#         data = user_data['trust']
#         response = self.client.post(reverse('user-create'), data=data)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#
#         self.client.credentials(HTTP_AUTHORIZATION='')
#         response = self.client.post(reverse('user-create'), data=data)
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#
#     def test_update_app_user(self):
#         pk = self.user.id
#
#         user_data = {
#             'update_email': {
#                 'email': 'user_update@vylo.com', 'name': 'user', 'username': 'user',
#                 'website': 'https://google.com/', 'bio': 'Some description about user',
#                 'phone': '', 'gender': 'other', 'is_active': True, 'is_source': False,
#                 'profile_photo': ''
#             },
#             'update_username': {
#                 'email': 'user_update@vylo.com', 'name': 'user_update', 'username': 'user_update',
#                 'website': 'https://google.com/', 'bio': 'Some description about user',
#                 'phone': '', 'gender': 'other', 'is_active': True, 'is_source': False,
#                 'profile_photo': ''
#             },
#             'update_other': {
#                 'email': 'user_update@vylo.com', 'name': 'user_update', 'username': 'user_update',
#                 'website': 'https://bing.com/', 'bio': 'Some description about app_user',
#                 'phone': '+380967678980', 'gender': 'male', 'is_active': False, 'is_source': False,
#                 'profile_photo': ''
#             }
#         }
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh_admin.access_token}')
#
#         data = user_data['update_email']
#         response = self.client.put(reverse('user-update', args=(pk,)), data=data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#         data = user_data['update_username']
#         response = self.client.put(reverse('user-update', args=(pk,)), data=data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#         data = user_data['update_other']
#         response = self.client.put(reverse('user-update', args=(pk,)), data=data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#         self.client.credentials(HTTP_AUTHORIZATION='')
#         response = self.client.put(reverse('user-update', args=(pk,)), data=data)
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#
#
# # TODO Upload photo
# class PublisherAPITestCase(APITestCase):
#     def setUp(self) -> None:
#         self.admin = User.objects.create(**users_data['admin'])
#         user = User.objects.create(**users_data['publ'])
#         publ = user.profile
#         publ.is_source = True
#         publ.save()
#         self.publ = publ
#
#         self.refresh_admin = RefreshToken.for_user(self.admin)
#
#     def test_list_publishers(self):
#         response = self.client.get(reverse('publ-list'))
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh_admin.access_token}')
#         response = self.client.get(reverse('publ-list'))
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#     def test_create_publisher(self):
#         publ_data = {
#             'email_in_use': {
#                 'email': 'publisher@vylo.com', 'name': 'app_publisher', 'username': 'app_publisher',
#                 'website': 'https://google.com/', 'bio': 'Some description about publisher',
#                 'phone': '', 'gender': 'other', 'is_active': True, 'is_source': True,
#                 'profile_photo': ''
#             },
#             'username_in_use': {
#                 'email': 'app_publisher@vylo.com', 'name': 'publisher', 'username': 'publisher',
#                 'website': 'https://google.com/', 'bio': 'Some description about publisher',
#                 'phone': '', 'gender': 'other', 'is_active': True, 'is_source': True,
#                 'profile_photo': ''
#             },
#             'trust': {
#                 'email': 'app_publisher@vylo.com', 'name': 'app_publisher', 'username': 'app_publisher',
#                 'website': 'https://google.com/', 'bio': 'Some description about publisher',
#                 'phone': '', 'gender': 'other', 'is_active': True, 'is_source': True,
#                 'profile_photo': ''
#             },
#         }
#         data = publ_data['email_in_use']
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh_admin.access_token}')
#         response = self.client.post(reverse('user-create'), data=data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#
#         data = publ_data['username_in_use']
#         response = self.client.post(reverse('user-create'), data=data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#
#         data = publ_data['trust']
#         response = self.client.post(reverse('user-create'), data=data)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#
#         self.client.credentials(HTTP_AUTHORIZATION='')
#         response = self.client.post(reverse('user-create'), data=data)
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#
#     def test_update_app_user(self):
#         pk = self.publ.id
#
#         publ_data = {
#             'update_email': {
#                 'email': 'publisher_update@vylo.com', 'name': 'publisher', 'username': 'publisher',
#                 'website': 'https://google.com/', 'bio': 'Some description about source',
#                 'phone': '', 'gender': 'other', 'is_active': True, 'is_source': True,
#                 'profile_photo': ''
#             },
#             'update_username': {
#                 'email': 'publisher_update@vylo.com', 'name': 'publ_update', 'username': 'publ_update',
#                 'website': 'https://google.com/', 'bio': 'Some description about source',
#                 'phone': '', 'gender': 'other', 'is_active': True, 'is_source': True,
#                 'profile_photo': ''
#             },
#             'update_other': {
#                 'email': 'publisher_update@vylo.com', 'name': 'publ_update', 'username': 'publ_update',
#                 'website': 'https://bing.com/', 'bio': 'Some description about app_source',
#                 'phone': '+380967678980', 'gender': 'male', 'is_active': False, 'is_source': True,
#                 'profile_photo': ''
#             }
#         }
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh_admin.access_token}')
#
#         data = publ_data['update_email']
#         response = self.client.put(reverse('user-update', args=(pk,)), data=data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#         data = publ_data['update_username']
#         response = self.client.put(reverse('user-update', args=(pk,)), data=data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#         data = publ_data['update_other']
#         response = self.client.put(reverse('user-update', args=(pk,)), data=data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#         self.client.credentials(HTTP_AUTHORIZATION='')
#         response = self.client.put(reverse('user-update', args=(pk,)), data=data)
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
