import json

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, generics, response, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.validators import ValidationError

from api.errors import SIGN_UP
from api.models import Profile
from api.pagination import NameIdPagination, SortOrderPagination, NamePagination
from api.serializers import (
    CategoriesSerializer,
    PublishersSerializer, PublishersV2Serializer
)
from api.views import (
    ActivateDraftUser, CreateDraftUser, AutoFollowList,
    MyProfile, ProfileDetails, CategoriesSubscription,
    UserNewsList, UserNews,
    PublishersList, NewsstandList, VyloPublishersList
)
from .serializers import (
    ProfileV2Serializer, ExternalProfileV2Serializer, MyColumnNewsV2Serializer
)


class MyProfileV2(MyProfile):
    serializer_class = ProfileV2Serializer


class ProfileDetailsV2(ProfileDetails):
    serializer_class = ExternalProfileV2Serializer


class MyCategoriesSubscription(generics.ListAPIView):
    serializer_class = CategoriesSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = NamePagination

    def get_queryset(self):
        return self.request.user.profile.categories_subscription


class MyPublishersSubscription(generics.ListAPIView):
    serializer_class = PublishersSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = NamePagination

    def get_queryset(self):
        return self.request.user.profile.publishers_subscription


class CategoriesSubscriptionV2(CategoriesSubscription):
    serializer_class = CategoriesSerializer

    @swagger_auto_schema(operation_description="Category subscribe. Send: single id or list of ids")
    def put(self, request, category_id, format=None):
        profile = request.user.profile
        categories = self.get_categories(category_id)
        for category in categories:
            profile.categories_subscription.add(category)
        profile.save()
        return response.Response(self.serializer_class(categories, many=True).data)

    @swagger_auto_schema(operation_description="Remove Category subscription. Send: single id or list of ids")
    def delete(self, request, category_id, format=None):
        profile = request.user.profile
        categories = self.get_categories(category_id)
        for category in categories:
            profile.categories_subscription.remove(category)
        profile.save()
        return response.Response(status=status.HTTP_204_NO_CONTENT)


class PublishersSubscriptionV2(views.APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PublishersV2Serializer

    @swagger_auto_schema(
        operation_description="Publisher subscribe. Send: single id or list of ids",
        manual_parameters=[
            openapi.Parameter(
                name="option",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                enum=["id", "global_id"],
                description="Option parameter to specify whether the provided IDs "
                            "are 'id' or 'global_id'. Default is 'id'.",
            )
        ],
    )
    def put(self, request, publisher_id, format=None):
        profile = request.user.profile
        option = request.query_params.get('option', 'pk')
        publishers = self.get_publishers(publisher_id, option).exclude(pk=profile.pk)
        for publisher in publishers:
            profile.publishers_subscription.add(publisher)
        profile.refresh_from_db()
        return response.Response(self.serializer_class(publishers, many=True, context={'profile': profile}).data)

    @swagger_auto_schema(
        operation_description="Publisher subscribe. Send: single id or list of ids",
        manual_parameters=[
            openapi.Parameter(
                name="option",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                enum=["id", "global_id"],
                description="Option parameter to specify whether the provided "
                            "IDs are 'id' or 'global_id'. Default is 'id'.",
            )
        ],
    )
    def delete(self, request, publisher_id, format=None):
        profile = request.user.profile
        option = request.query_params.get('option', 'pk')
        publishers = self.get_publishers(publisher_id, option).exclude(pk=profile.pk)
        for publisher in publishers:
            profile.publishers_subscription.remove(publisher)
        profile.save()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def get_publishers(publisher_id, option='pk'):
        if option == 'global_id':
            return Profile.objects.filter(global_id=publisher_id)

        publisher_id_lst = json.loads(publisher_id)
        if type(publisher_id_lst) != list:
            publisher_id_lst = [publisher_id_lst]
        return Profile.objects.filter(pk__in=publisher_id_lst, is_source=False)


class PublishersListV2(PublishersList):
    pagination_class = NameIdPagination


class NewsstandListV2(NewsstandList):
    pagination_class = NameIdPagination


class VyloPublishersListV2(VyloPublishersList):
    pagination_class = NameIdPagination


class UserNewsListV2(UserNewsList):
    serializer_class = MyColumnNewsV2Serializer


class UserNewsV2(UserNews):
    serializer_class = MyColumnNewsV2Serializer


class CreateDraftUserV2(CreateDraftUser):

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        is_valid = serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return response.Response({'is_valid': is_valid}, status=status.HTTP_201_CREATED)


class ActivateDraftUserV2(ActivateDraftUser):

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        is_valid = serializer.is_valid(raise_exception=True)
        is_active = serializer.activate(kwargs.get(self.lookup_field))
        if not is_active:
            raise ValidationError({'code': [SIGN_UP['EMAIL_VERIFICATION']]})
        return response.Response({'is_valid': is_valid and is_active}, status=status.HTTP_200_OK)


class AutoFollowListV2(AutoFollowList):
    pagination_class = SortOrderPagination
