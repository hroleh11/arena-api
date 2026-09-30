import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.http import (
    Http404
)
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, parsers, generics, permissions, filters
from rest_framework.exceptions import ErrorDetail
from rest_framework.response import Response
from rest_framework.views import APIView

from api.errors import EDIT_PROFILE
from api.models import Categories, Profile, BlockedProfiles
from api.pagination import NamePagination
from api.serializers.profile import (
    ProfileSerializer, ProfileImageSaveSerializer,
    ReportProfilesSerializer, BlockProfilesSerializer,
    BlockProfileListSerializer, ProfileWebSerializer,
    ExternalProfileSerializer, QRCodeSerializer
)
from api.serializers.publishers import FollowersSerializer, FollowingSerializer
from column.celery import app

User = get_user_model()


class MyProfile(generics.RetrieveUpdateDestroyAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user.profile

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        is_valid = serializer.is_valid(raise_exception=False)
        if is_valid:
            self.perform_update(serializer)

            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}

            return Response(serializer.data)

        if settings.DEBUG:
            print(serializer.errors)    # TODO catch errors at log file
        return Response(
            data={'detail': [ErrorDetail(EDIT_PROFILE['PROFILE'], code='invalid')]},
            status=status.HTTP_400_BAD_REQUEST
        )

    def destroy(self, request, *args, **kwargs):
        user = request.user

        profile = user.profile
        profile.publishers_subscription.set(list(), clear=False)
        profile.prof_subscribers.set(list(), clear=False)

        user.is_active = False
        user.save(update_fields=['is_active'])
        return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "option",
                openapi.IN_QUERY,
                description="Options: username or global_id",
                type=openapi.TYPE_STRING,
            )
        ]
    ),
)
class ProfileDetails(generics.RetrieveAPIView):
    queryset = Profile.objects.filter(user__is_active=True)
    serializer_class = ExternalProfileSerializer
    permission_classes = [permissions.IsAuthenticated, ]
    lookup_field = 'unique_value'
    lookup_url_kwarg = 'option'

    def get_object(self):
        unique_value = self.kwargs.get(self.lookup_field)
        option = self.request.query_params.get(self.lookup_url_kwarg, '')
        if option.lower() == 'username':
            user = get_object_or_404(User, username=unique_value)
            return user.profile

        try:
            profile = get_object_or_404(Profile, global_id=unique_value)
        except ValidationError:
            raise Http404()

        return profile


class ProfileImage(APIView):
    permission_classes = [permissions.IsAuthenticated, ]
    parser_classes = (parsers.MultiPartParser, parsers.FormParser,)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='profile_photo',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                description='Profile Photo'
            ),
        ],
    )
    def post(self, request, format=None):
        profile = request.user.profile

        ext = request.data['profile_photo'].name.split('.')[-1]
        if profile.profile_photo:
            name = profile.profile_photo.name.split('/')[-1]
            counter = name[name.rfind('_') + 1:name.rfind('.')]
            request.data['profile_photo'].name = f'profile{profile.global_id}_{counter}.{ext}'

        else:
            request.data['profile_photo'].name = f'profile{profile.global_id}_0000.{ext}'

        serializer = ProfileImageSaveSerializer(profile, data=request.data)

        if serializer.is_valid():
            profile.profile_photo.delete(save=False)
            serializer.save()
            app.send_task('column.tasks.update_profile_image',
                          args=[profile.global_id, profile.profile_photo.name],
                          queue='feed')

            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionsView(APIView):
    permissions = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        profile = request.user.profile
        return Response({
            'categories_subscription': profile.categories_subscription.values_list('global_id', flat=True),
            'publishers_subscription': profile.publishers_subscription.values_list('global_id', flat=True)
        }, status=status.HTTP_200_OK)


# @method_decorator(
#     name="put",
#     decorator=swagger_auto_schema(
#         manual_parameters=[
#             openapi.Parameter(
#                 "category_id",
#                 openapi.IN_QUERY,
#                 description="Category ID: single id or list of ids",
#                 type=openapi.TYPE_STRING,
#             )
#         ]
#     ),
# )
class CategoriesSubscription(APIView):
    permission_classes = [permissions.IsAuthenticated, ]
    serializer_class = ProfileSerializer

    @swagger_auto_schema(
        operation_description="Category subscribe. Send: single id or list of ids"
        # manual_parameters=[
        #     openapi.Parameter(
        #         "category_id",
        #         openapi.IN_QUERY,
        #         type=openapi.TYPE_STRING,
        #         description="Category ID: single id or list of ids",
        #     ),
        # ],
    )
    def put(self, request, category_id, format=None):
        profile = request.user.profile
        categories = self.get_categories(category_id)
        for category in categories:
            profile.categories_subscription.add(category)
        profile.save()
        return Response(self.serializer_class(profile).data)

    @swagger_auto_schema(
        operation_description="Remove Category subscription. Send: single id or list of ids")
    def delete(self, request, category_id, format=None):
        profile = request.user.profile
        categories = self.get_categories(category_id)
        for category in categories:
            profile.categories_subscription.remove(category)
        profile.save()
        return Response(self.serializer_class(profile).data)

    @staticmethod
    def get_categories(category_id):
        category_id_lst = json.loads(category_id)
        if type(category_id_lst) != list:
            category_id_lst = [category_id_lst]
        return Categories.objects.filter(pk__in=category_id_lst, is_active=True).order_by('name')


class PublishersSubscription(APIView):
    permission_classes = [permissions.IsAuthenticated, ]
    serializer_class = ProfileSerializer

    @swagger_auto_schema(
        operation_description="Publisher subscribe. Send: single id or list of ids")
    def put(self, request, publisher_id, format=None):
        profile = request.user.profile
        publishers = self.get_publishers(publisher_id).exclude(pk=profile.pk)
        for publisher in publishers:
            profile.publishers_subscription.add(publisher)
        profile.save()
        return Response(self.serializer_class(profile).data)

    @swagger_auto_schema(
        operation_description="Remove Publisher subscription. Send: single id or list of ids")
    def delete(self, request, publisher_id, format=None):
        profile = request.user.profile
        publishers = self.get_publishers(publisher_id).exclude(pk=profile.pk)
        for publisher in publishers:
            profile.publishers_subscription.remove(publisher)
        profile.save()
        return Response(self.serializer_class(profile).data)

    @staticmethod
    def get_publishers(publisher_id):
        publisher_id_lst = json.loads(publisher_id)
        if type(publisher_id_lst) != list:
            publisher_id_lst = [publisher_id_lst]
        return Profile.objects.filter(pk__in=publisher_id_lst, is_source=False)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "profile_global_id",
                openapi.IN_QUERY,
                description="Profile global id",
                type=openapi.TYPE_STRING,
            )
        ]
    ),
)
class FollowABCView(generics.ListAPIView):
    serializer_class = None
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = NamePagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)

    def get_object(self):
        profile_global_id = self.request.query_params.get('profile_global_id')
        if profile_global_id:
            profile = get_object_or_404(Profile, global_id=profile_global_id, user__is_active=True)
        else:
            profile = self.request.user.profile
        return profile


class FollowingView(FollowABCView):
    serializer_class = FollowingSerializer

    def get_queryset(self):
        profile = self.get_object()
        return profile.publishers_subscription.all()


class FollowersView(FollowABCView):
    serializer_class = FollowersSerializer

    def get_queryset(self):
        profile = self.get_object()
        return profile.prof_subscribers.all()


class ReportView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReportProfilesSerializer


class BlockView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BlockProfilesSerializer
    pagination_class = None

    def list(self, request, *args, **kwargs):
        serializer = BlockProfileListSerializer(request.user.profile.i_block_users.all(), many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class BlockDestroyView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'global_id'

    def get_object(self):
        blocked_profile_global_id = self.kwargs.get(self.lookup_field)
        return get_object_or_404(BlockedProfiles, profile=self.request.user.profile,
                                 blocked_profile__global_id=blocked_profile_global_id)


class ProfileWebView(generics.RetrieveAPIView):
    lookup_field = 'username'
    serializer_class = ProfileWebSerializer
    permission_classes = (permissions.AllowAny,)

    def get_object(self):
        username = self.kwargs.get(self.lookup_field)
        return get_object_or_404(Profile, user__username=username, is_source=False)


class ProfileQRCode(generics.RetrieveAPIView):
    queryset = Profile.objects.all()
    serializer_class = QRCodeSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user.profile
