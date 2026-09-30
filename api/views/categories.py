from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, filters, views
from rest_framework.response import Response

from api.models import Categories
from api.pagination import NamePagination
from api.serializers import categories


class CategoriesList(generics.ListAPIView):
    queryset = Categories.objects.filter(is_active=True, is_optional=True, parent=None).order_by('name')
    serializer_class = categories.CategoriesSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = NamePagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)



@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "screen",
                openapi.IN_QUERY,
                description="newsstand or sportsbook",
                type=openapi.TYPE_STRING,
            ),
        ]
    ),
)
class CategoriesNavigation(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        screen = request.query_params.get('screen', None)
        queryset = Categories.objects.filter(is_active=True, is_optional=True)

        exclude_kwargs = {}

        parent_queryset = queryset.filter(is_active=True, is_optional=True, parent__isnull=True).order_by('filter_order')
        child_queryset = list()
        for parent in parent_queryset:
            child_queryset.extend(parent.subcategories.filter(
                is_active=True, is_optional=True
            ).order_by('filter_order').exclude(**exclude_kwargs))
        return Response({
            'categories': categories.ParentCategoriesNavigation(parent_queryset, many=True).data,
            'subcategories': categories.ChildCategoriesNavigation(child_queryset, many=True, context={
                'profile': request.user.profile
            }).data
        })


class SubcategoriesList(views.APIView):
    lookup_field = 'global_id'

    def get_object(self):
        global_id = self.kwargs.get(self.lookup_field)
        queryset = Categories.objects.filter(global_id=global_id)
        return get_object_or_404(queryset)

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response({
            'subcategories': instance.subcategories.filter(is_active=True)
                                                   .values_list('global_id', flat=True)
        })


class FavouriteCategoriesList(generics.ListAPIView):
    queryset = Categories.objects.filter(is_active=True, parent=None).order_by('name')
    serializer_class = categories.FavouriteCategoriesSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = NamePagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)


class CategoriesMain(views.APIView):
    permission_classes = (permissions.AllowAny,)

    serializer_class = categories.CategoriesSerializer
    response_serializer = categories.CategoriesSerializer

    def get(self, request, *args, **kwargs):
        parent_categories = Categories.objects.filter(
            is_active=True, 
            parent__isnull=True,
            category_type='main'
        ).order_by('order')
        
        result = []
        context = {}
        if request.user.is_authenticated:
            context['profile'] = request.user.profile
        
        for parent in parent_categories:
            subcategories = parent.subcategories.filter(
                is_active=True,
                category_type='main'
            ).order_by('order')
            
            parent_data = categories.CategoriesSerializer(parent, context=context).data
            parent_data['subcategories'] = categories.CategoriesSerializer(subcategories, many=True, context=context).data
            
            result.append(parent_data)
        
        return Response(result)
