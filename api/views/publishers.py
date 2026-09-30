# from django.contrib.postgres.search import SearchVector
from django.utils.decorators import method_decorator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, generics, filters
from rest_framework.pagination import PageNumberPagination

from api.models import Profile
from api.serializers import publishers


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="Search string",
                type=openapi.TYPE_STRING,
            ),
        ]
    ),
)
class PublishersList(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = publishers.PublishersSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name', 'user__username')
    queryset = Profile.objects.filter(user__is_active=True, user__isnull=False).order_by('name')
    pagination_class = PageNumberPagination


class NewsstandList(PublishersList):
    queryset = Profile.objects.filter(
        user__is_active=True, user__isnull=False, is_source=True).order_by('name')


class VyloPublishersList(PublishersList):
    queryset = Profile.objects.filter(
        user__is_active=True, user__isnull=False, is_source=False).order_by('name')
